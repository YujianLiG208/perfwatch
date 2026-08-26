from __future__ import annotations

import ctypes
import signal
import sys
import threading
from collections.abc import Mapping
from ctypes import wintypes
from typing import Any

import httpx

from perfwatch.overlay.model import OverlayModel, model_from_snapshot, stale_model

WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_PAINT = 0x000F
WM_NCHITTEST = 0x0084
WM_APP_UPDATE = 0x8001
HTTRANSPARENT = -1

WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TRANSPARENT = 0x00000020
WS_POPUP = 0x80000000

LWA_ALPHA = 0x00000002
SPI_GETWORKAREA = 0x0030
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
TRANSPARENT = 1
DT_LEFT = 0x0000
DT_TOP = 0x0000
DT_NOPREFIX = 0x0800
DT_WORDBREAK = 0x0010
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000

WINDOW_WIDTH = 350
WINDOW_HEIGHT = 166
WINDOW_MARGIN = 16

LRESULT = ctypes.c_ssize_t
WNDPROC = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", wintypes.HDC),
        ("fErase", wintypes.BOOL),
        ("rcPaint", wintypes.RECT),
        ("fRestore", wintypes.BOOL),
        ("fIncUpdate", wintypes.BOOL),
        ("rgbReserved", wintypes.BYTE * 32),
    ]


def _windows_libraries() -> tuple[Any, Any, Any]:
    if sys.platform != "win32":
        raise RuntimeError("Win32 overlay requires Windows")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    return user32, gdi32, kernel32


class Win32OverlayWindow:
    def __init__(self) -> None:
        self.hwnd = 0
        self._model = stale_model(None)
        self._model_lock = threading.Lock()
        self._user32: Any = None
        self._gdi32: Any = None
        self._kernel32: Any = None
        self._font = 0
        self._instance = 0
        self._class_name = f"PerfWatchOverlayWindow_{id(self):x}"
        self._wndproc = WNDPROC(self._window_proc)

    def create(self) -> int:
        self._user32, self._gdi32, self._kernel32 = _windows_libraries()
        self._configure_functions()
        self._instance = int(self._kernel32.GetModuleHandleW(None) or 0)
        window_class = WNDCLASSW(
            lpfnWndProc=self._wndproc,
            hInstance=self._instance,
            lpszClassName=self._class_name,
        )
        if not self._user32.RegisterClassW(ctypes.byref(window_class)):
            raise ctypes.WinError(ctypes.get_last_error())

        self._font = int(
            self._gdi32.CreateFontW(
                -16,
                0,
                0,
                0,
                400,
                False,
                False,
                False,
                1,
                0,
                0,
                5,
                0,
                "Segoe UI",
            )
            or 0
        )
        work_area = wintypes.RECT()
        if not self._user32.SystemParametersInfoW(
            SPI_GETWORKAREA, 0, ctypes.byref(work_area), 0
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        x = work_area.right - WINDOW_WIDTH - WINDOW_MARGIN
        y = work_area.top + WINDOW_MARGIN
        extended_style = (
            WS_EX_LAYERED
            | WS_EX_TOPMOST
            | WS_EX_TOOLWINDOW
            | WS_EX_NOACTIVATE
            | WS_EX_TRANSPARENT
        )
        hwnd = self._user32.CreateWindowExW(
            extended_style,
            self._class_name,
            "PerfWatch",
            WS_POPUP,
            x,
            y,
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
            None,
            None,
            self._instance,
            None,
        )
        if not hwnd:
            raise ctypes.WinError(ctypes.get_last_error())
        self.hwnd = int(hwnd)
        if not self._user32.SetLayeredWindowAttributes(self.hwnd, 0, 220, LWA_ALPHA):
            raise ctypes.WinError(ctypes.get_last_error())
        if not self._user32.SetWindowPos(
            self.hwnd,
            ctypes.c_void_p(-1),
            x,
            y,
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
            SWP_NOACTIVATE | SWP_SHOWWINDOW,
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return self.hwnd

    def update(self, model: OverlayModel) -> None:
        with self._model_lock:
            self._model = model
        if self.hwnd:
            self._user32.PostMessageW(self.hwnd, WM_APP_UPDATE, 0, 0)

    def close(self) -> None:
        if self.hwnd:
            self._user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)

    def run(self) -> None:
        if not self.hwnd:
            raise RuntimeError("overlay window has not been created")
        message = wintypes.MSG()
        try:
            while True:
                result = self._user32.GetMessageW(ctypes.byref(message), None, 0, 0)
                if result == 0:
                    break
                if result == -1:
                    raise ctypes.WinError(ctypes.get_last_error())
                self._user32.TranslateMessage(ctypes.byref(message))
                self._user32.DispatchMessageW(ctypes.byref(message))
        finally:
            if self._font:
                self._gdi32.DeleteObject(self._font)
                self._font = 0
            self._user32.UnregisterClassW(self._class_name, self._instance)

    def _window_proc(self, hwnd: int, message: int, wparam: int, lparam: int) -> int:
        if message == WM_NCHITTEST:
            return HTTRANSPARENT
        if message == WM_APP_UPDATE:
            self._user32.InvalidateRect(hwnd, None, True)
            return 0
        if message == WM_PAINT:
            self._paint(hwnd)
            return 0
        if message == WM_CLOSE:
            self._user32.DestroyWindow(hwnd)
            return 0
        if message == WM_DESTROY:
            self.hwnd = 0
            self._user32.PostQuitMessage(0)
            return 0
        return int(self._user32.DefWindowProcW(hwnd, message, wparam, lparam))

    def _paint(self, hwnd: int) -> None:
        paint = PAINTSTRUCT()
        hdc = self._user32.BeginPaint(hwnd, ctypes.byref(paint))
        try:
            rectangle = wintypes.RECT()
            self._user32.GetClientRect(hwnd, ctypes.byref(rectangle))
            brush = self._gdi32.CreateSolidBrush(0x00202020)
            try:
                self._user32.FillRect(hdc, ctypes.byref(rectangle), brush)
            finally:
                self._gdi32.DeleteObject(brush)
            self._gdi32.SetBkMode(hdc, TRANSPARENT)
            self._gdi32.SetTextColor(hdc, 0x00F0F0F0)
            previous_font = self._gdi32.SelectObject(hdc, self._font) if self._font else 0
            with self._model_lock:
                text = "\n".join(self._model.lines)
            text_rectangle = wintypes.RECT(12, 10, WINDOW_WIDTH - 12, WINDOW_HEIGHT - 10)
            self._user32.DrawTextW(
                hdc,
                text,
                -1,
                ctypes.byref(text_rectangle),
                DT_LEFT | DT_TOP | DT_NOPREFIX | DT_WORDBREAK,
            )
            if previous_font:
                self._gdi32.SelectObject(hdc, previous_font)
        finally:
            self._user32.EndPaint(hwnd, ctypes.byref(paint))

    def _configure_functions(self) -> None:
        self._kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        self._kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        self._kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self._kernel32.WaitForSingleObject.restype = wintypes.DWORD
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
        self._user32.RegisterClassW.restype = wintypes.ATOM
        self._user32.CreateWindowExW.argtypes = [
            wintypes.DWORD,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.DWORD,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.HWND,
            wintypes.HANDLE,
            wintypes.HINSTANCE,
            wintypes.LPVOID,
        ]
        self._user32.CreateWindowExW.restype = wintypes.HWND
        self._user32.SetLayeredWindowAttributes.argtypes = [
            wintypes.HWND,
            wintypes.DWORD,
            wintypes.BYTE,
            wintypes.DWORD,
        ]
        self._user32.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        self._user32.SystemParametersInfoW.argtypes = [
            wintypes.UINT,
            wintypes.UINT,
            wintypes.LPVOID,
            wintypes.UINT,
        ]
        self._user32.PostMessageW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        self._user32.GetMessageW.argtypes = [
            ctypes.POINTER(wintypes.MSG),
            wintypes.HWND,
            wintypes.UINT,
            wintypes.UINT,
        ]
        self._user32.GetMessageW.restype = wintypes.BOOL
        self._user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
        self._user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
        self._user32.DispatchMessageW.restype = LRESULT
        self._user32.DestroyWindow.argtypes = [wintypes.HWND]
        self._user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
        self._user32.InvalidateRect.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.RECT),
            wintypes.BOOL,
        ]
        self._user32.GetClientRect.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.RECT),
        ]
        self._user32.DefWindowProcW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        self._user32.DefWindowProcW.restype = LRESULT
        self._user32.BeginPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
        self._user32.BeginPaint.restype = wintypes.HDC
        self._user32.EndPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
        self._user32.FillRect.argtypes = [
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            wintypes.HBRUSH,
        ]
        self._user32.DrawTextW.argtypes = [
            wintypes.HDC,
            wintypes.LPCWSTR,
            ctypes.c_int,
            ctypes.POINTER(wintypes.RECT),
            wintypes.UINT,
        ]
        self._gdi32.CreateFontW.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPCWSTR,
        ]
        self._gdi32.CreateFontW.restype = wintypes.HFONT
        self._gdi32.CreateSolidBrush.argtypes = [wintypes.DWORD]
        self._gdi32.CreateSolidBrush.restype = wintypes.HBRUSH
        self._gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
        self._gdi32.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
        self._gdi32.SetTextColor.argtypes = [wintypes.HDC, wintypes.DWORD]
        self._gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
        self._gdi32.SelectObject.restype = wintypes.HGDIOBJ


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
        parent_handle = 0
        if parent_pid is not None:
            parent_handle = int(
                window._kernel32.OpenProcess(SYNCHRONIZE, False, parent_pid) or 0
            )
        try:
            with httpx.Client(timeout=0.5) as client:
                while not stop_event.is_set():
                    if parent_handle and (
                        window._kernel32.WaitForSingleObject(parent_handle, 0) == WAIT_OBJECT_0
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
                window._kernel32.CloseHandle(parent_handle)

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
