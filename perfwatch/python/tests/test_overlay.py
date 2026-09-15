from copy import deepcopy
import sys

import pytest

from perfwatch.collectors.mock import get_mock_snapshot
from perfwatch.overlay import model_from_snapshot, stale_model
from perfwatch.overlay.win32 import Win32OverlayWindow


def test_overlay_models_live_unavailable_waiting_and_stale_states() -> None:
    snapshot = deepcopy(get_mock_snapshot())
    snapshot["cpu"]["package_power_watts"] = None
    snapshot["battery"]["estimated_remaining_seconds"] = None

    live = model_from_snapshot(snapshot)
    assert live.status == "live"
    assert "CPU 42.5%" in live.lines[0]
    assert any("Power N/A" in line for line in live.lines)
    assert any("Battery 78.0%" in line for line in live.lines)

    waiting = stale_model(None)
    assert waiting.status == "waiting"
    assert waiting.lines == ("Waiting for service",)

    stale = stale_model(live)
    assert stale.status == "stale"
    assert stale.lines[-1] == "STALE"


@pytest.mark.skipif(sys.platform != "win32", reason="Win32-only smoke")
def test_overlay_window_creates_and_exits_cleanly(monkeypatch) -> None:
    import win32con
    import win32gui

    drawn_text = []
    draw_text = win32gui.DrawText

    def record_draw(hdc, text, *args):
        result = draw_text(hdc, text, *args)
        drawn_text.append(text)
        return result

    monkeypatch.setattr(win32gui, "DrawText", record_draw)
    window = Win32OverlayWindow()
    hwnd = window.create()
    try:
        required_style = (
            win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW
            | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TRANSPARENT
        )
        assert win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & required_style == required_style
        assert win32gui.GetClientRect(hwnd) == (0, 0, 350, 166)
        assert win32gui.GetLayeredWindowAttributes(hwnd) == (0, 220, win32con.LWA_ALPHA)
        assert win32gui.SendMessage(hwnd, win32con.WM_NCHITTEST, 0, 0) == win32con.HTTRANSPARENT

        model = model_from_snapshot(get_mock_snapshot())
        window.update(model)
        win32gui.PumpWaitingMessages()
        win32gui.UpdateWindow(hwnd)
        assert "\n".join(model.lines) in drawn_text
    finally:
        window.close()
        window.run()
    assert not win32gui.IsWindow(hwnd)
    assert window.hwnd == window._font == 0
