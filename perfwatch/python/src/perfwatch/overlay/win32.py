from __future__ import annotations

import signal
import sys
import threading
from collections.abc import Mapping

import httpx

if sys.platform == "win32":
    import win32api
    import win32con
    import win32event
    import win32gui
    import winerror

from perfwatch.overlay.model import OverlayModel, model_from_snapshot, stale_model

WM_APP_UPDATE = 0x8001
WINDOW_WIDTH = 350
WINDOW_HEIGHT = 166
WINDOW_MARGIN = 16


class Win32OverlayWindow:
    def __init__(self) -> None:
        self.hwnd = 0
        self._model = stale_model(None)
        self._model_lock = threading.Lock()
        self._font = 0
        self._instance = 0
        self._class_name = f"PerfWatchOverlayWindow_{id(self):x}"

    def create(self) -> int:
        if sys.platform != "win32":
            raise RuntimeError("Win32 overlay requires Windows")
        self._instance = win32api.GetModuleHandle(None)
        window_class = win32gui.WNDCLASS()
        window_class.lpfnWndProc = self._window_proc
        window_class.hInstance = self._instance
        window_class.lpszClassName = self._class_name
        win32gui.RegisterClass(window_class)

        font = win32gui.LOGFONT()
        font.lfHeight = -16
        font.lfWeight = win32con.FW_NORMAL
        font.lfCharSet = win32con.DEFAULT_CHARSET
        font.lfQuality = win32con.CLEARTYPE_QUALITY
        font.lfFaceName = "Segoe UI"
        self._font = win32gui.CreateFontIndirect(font)
        work_area = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0, 0)))["Work"]
        x = work_area[2] - WINDOW_WIDTH - WINDOW_MARGIN
        y = work_area[1] + WINDOW_MARGIN
        extended_style = (
            win32con.WS_EX_LAYERED
            | win32con.WS_EX_TOPMOST
            | win32con.WS_EX_TOOLWINDOW
            | win32con.WS_EX_NOACTIVATE
            | win32con.WS_EX_TRANSPARENT
        )
        self.hwnd = win32gui.CreateWindowEx(
            extended_style,
            self._class_name,
            "PerfWatch",
            win32con.WS_POPUP,
            x,
            y,
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
            None,
            None,
            self._instance,
            None,
        )
        win32gui.SetLayeredWindowAttributes(self.hwnd, 0, 220, win32con.LWA_ALPHA)
        win32gui.SetWindowPos(
            self.hwnd,
            win32con.HWND_TOPMOST,
            x,
            y,
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
            win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW,
        )
        return self.hwnd

    def update(self, model: OverlayModel) -> None:
        with self._model_lock:
            self._model = model
        self._post_message(WM_APP_UPDATE)

    def close(self) -> None:
        if self.hwnd:
            self._post_message(win32con.WM_CLOSE)

    def _post_message(self, message: int) -> None:
        if self.hwnd:
            try:
                win32gui.PostMessage(self.hwnd, message, 0, 0)
            except win32gui.error as error:
                # The UI thread may destroy the window while the worker posts an update.
                if error.winerror != winerror.ERROR_INVALID_WINDOW_HANDLE:
                    raise

    def run(self) -> None:
        if not self.hwnd:
            raise RuntimeError("overlay window has not been created")
        try:
            win32gui.PumpMessages()
        finally:
            if self._font:
                win32gui.DeleteObject(self._font)
                self._font = 0
            win32gui.UnregisterClass(self._class_name, self._instance)

    def _window_proc(self, hwnd: int, message: int, wparam: int, lparam: int) -> int:
        if message == win32con.WM_NCHITTEST:
            return win32con.HTTRANSPARENT
        if message == WM_APP_UPDATE:
            win32gui.InvalidateRect(hwnd, None, True)
            return 0
        if message == win32con.WM_PAINT:
            self._paint(hwnd)
            return 0
        if message == win32con.WM_CLOSE:
            win32gui.DestroyWindow(hwnd)
            return 0
        if message == win32con.WM_DESTROY:
            self.hwnd = 0
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, message, wparam, lparam)

    def _paint(self, hwnd: int) -> None:
        hdc, paint = win32gui.BeginPaint(hwnd)
        try:
            rectangle = win32gui.GetClientRect(hwnd)
            brush = win32gui.CreateSolidBrush(0x00202020)
            try:
                win32gui.FillRect(hdc, rectangle, brush)
            finally:
                win32gui.DeleteObject(brush)
            win32gui.SetBkMode(hdc, win32con.TRANSPARENT)
            win32gui.SetTextColor(hdc, 0x00F0F0F0)
            previous_font = win32gui.SelectObject(hdc, self._font) if self._font else 0
            try:
                with self._model_lock:
                    text = "\n".join(self._model.lines)
                win32gui.DrawText(
                    hdc,
                    text,
                    -1,
                    (12, 10, WINDOW_WIDTH - 12, WINDOW_HEIGHT - 10),
                    win32con.DT_LEFT | win32con.DT_TOP | win32con.DT_NOPREFIX | win32con.DT_WORDBREAK,
                )
            finally:
                if previous_font:
                    win32gui.SelectObject(hdc, previous_font)
        finally:
            win32gui.EndPaint(hwnd, paint)


def run_overlay(
    snapshot_url: str = "http://127.0.0.1:8000/snapshot",
    interval_seconds: float = 1.0,
    parent_pid: int | None = None,
) -> None:
    window = Win32OverlayWindow()
    window.create()
    stop_event = threading.Event()

    def fetch_snapshots() -> None:
        previous: OverlayModel | None = None
        parent_handle = None
        if parent_pid is not None:
            try:
                parent_handle = win32api.OpenProcess(win32con.SYNCHRONIZE, False, parent_pid)
            except win32api.error:
                # Keep HTTP updates when the parent cannot be opened, as before.
                pass
        try:
            with httpx.Client(timeout=0.5) as client:
                while not stop_event.is_set():
                    if parent_handle and (
                        win32event.WaitForSingleObject(parent_handle, 0) == win32event.WAIT_OBJECT_0
                    ):
                        window.close()
                        return
                    try:
                        response = client.get(snapshot_url)
                        response.raise_for_status()
                        snapshot = response.json()
                        if not isinstance(snapshot, Mapping):
                            raise ValueError("snapshot response must be an object")
                        previous = model_from_snapshot(snapshot)
                    except (httpx.HTTPError, TypeError, ValueError):
                        previous = stale_model(previous)
                    window.update(previous)
                    stop_event.wait(interval_seconds)
        finally:
            if parent_handle:
                parent_handle.Close()

    worker = threading.Thread(target=fetch_snapshots, name="perfwatch-overlay-http", daemon=True)
    worker.start()
    previous_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, lambda _signum, _frame: window.close())
    try:
        window.run()
    except KeyboardInterrupt:
        window.close()
    finally:
        stop_event.set()
        worker.join(timeout=max(interval_seconds, 0.5) + 1.0)
        signal.signal(signal.SIGINT, previous_sigint)
