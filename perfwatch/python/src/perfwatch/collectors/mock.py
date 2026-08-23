from __future__ import annotations

from typing import Any

MOCK_TIMESTAMP_MS = 1710000000000


def _triangle(sample_index: int, period: int) -> int:
    position = sample_index % period
    half_period = period // 2
    return position if position <= half_period else period - position


def get_mock_snapshot(sample_index: int = 0) -> dict[str, Any]:
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")

    triangle = _triangle(sample_index, 20)
    battery_triangle = _triangle(sample_index, 80)
    battery_position = sample_index % 80
    return {
        "timestamp_ms": MOCK_TIMESTAMP_MS + sample_index * 1_000,
        "cpu": {
            "usage_percent": 42.5 + 1.5 * triangle,
            "frequency_mhz": 3600.0 + 20.0 * triangle,
            "package_power_watts": 35.0 + 0.8 * triangle,
            "temperature_celsius": 65.0 + 0.4 * triangle,
        },
        "memory": {
            "total_bytes": 34359738368,
            "used_bytes": 17179869184 + 67108864 * triangle,
        },
        "battery": {
            "available": True,
            "charging": battery_position > 40,
            "percent": 78.0 - 0.25 * battery_triangle,
            "power_watts": 18.5 + 0.3 * triangle,
            "energy_remaining_wh": 45.0 - 0.2 * battery_triangle,
        },
        "gpu": {
            "available": False,
            "vendor": "unavailable",
            "usage_percent": 0.0,
            "vram_total_bytes": 0,
            "vram_used_bytes": 0,
            "power_watts": 0.0,
            "temperature_celsius": 0.0,
        },
        "top_processes": [
            {
                "pid": 1234,
                "name": "mock_process",
                "cpu_percent": 12.5 + 0.7 * triangle,
                "rss_bytes": 268435456 + 4194304 * triangle,
                "vram_bytes": 0,
                "estimated_power_score": 0.42 + 0.01 * triangle,
            }
        ],
    }


class MockCollector:
    def __init__(self) -> None:
        self._sample_index = 0

    def collect(self) -> dict[str, Any]:
        snapshot = get_mock_snapshot(self._sample_index)
        self._sample_index += 1
        return snapshot
