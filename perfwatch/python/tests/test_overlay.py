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
def test_overlay_window_creates_and_exits_cleanly() -> None:
    window = Win32OverlayWindow()
    assert window.create()
    window.close()
    window.run()
