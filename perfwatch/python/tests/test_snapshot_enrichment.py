from __future__ import annotations

from typing import Any

import pytest

from perfwatch.analytics.snapshot import enrich_snapshot


def test_enrich_snapshot_computes_battery_and_process_estimates() -> None:
    snapshot: dict[str, Any] = {
        "battery": {
            "available": True,
            "charging": False,
            "energy_remaining_wh": 45.0,
            "power_watts": 18.5,
        },
        "top_processes": [
            {
                "cpu_percent": 12.5,
                "rss_bytes": 268_435_456,
                "vram_bytes": 0,
                "estimated_power_score": 0.42,
            }
        ],
    }

    result = enrich_snapshot(snapshot)

    assert result is snapshot
    assert snapshot["battery"]["estimated_remaining_seconds"] == pytest.approx(
        8_756.756756756757
    )
    assert snapshot["top_processes"][0]["estimated_power_score"] == pytest.approx(0.1)


@pytest.mark.parametrize(
    "battery",
    [
        {
            "available": True,
            "charging": True,
            "energy_remaining_wh": 45.0,
            "power_watts": 18.5,
        },
        {
            "available": False,
            "charging": False,
            "energy_remaining_wh": 45.0,
            "power_watts": 18.5,
        },
        {
            "available": True,
            "charging": False,
            "energy_remaining_wh": 45.0,
            "power_watts": 0.0,
        },
        {"available": True, "charging": False, "power_watts": 18.5},
        {
            "available": True,
            "charging": False,
            "energy_remaining_wh": True,
            "power_watts": 18.5,
        },
        {
            "available": True,
            "charging": False,
            "energy_remaining_wh": 45.0,
            "power_watts": "18.5",
        },
    ],
)
def test_enrich_snapshot_uses_none_for_unusable_battery_inputs(
    battery: dict[str, object],
) -> None:
    snapshot: dict[str, Any] = {"battery": battery}

    enrich_snapshot(snapshot)

    assert snapshot["battery"]["estimated_remaining_seconds"] is None


@pytest.mark.parametrize(
    "process",
    [
        {"rss_bytes": 268_435_456, "vram_bytes": 0},
        {"cpu_percent": True, "rss_bytes": 268_435_456, "vram_bytes": 0},
        {"cpu_percent": -1.0, "rss_bytes": 268_435_456, "vram_bytes": 0},
        {"cpu_percent": 12.5, "rss_bytes": -1, "vram_bytes": 0},
        {"cpu_percent": 12.5, "rss_bytes": 1.5, "vram_bytes": 0},
        {"cpu_percent": 12.5, "rss_bytes": 268_435_456, "vram_bytes": None},
    ],
)
def test_enrich_snapshot_preserves_process_with_unusable_inputs(
    process: dict[str, object],
) -> None:
    snapshot: dict[str, Any] = {"top_processes": [process]}

    enrich_snapshot(snapshot)

    assert snapshot["top_processes"] == [process]
    assert process["estimated_power_score"] is None
