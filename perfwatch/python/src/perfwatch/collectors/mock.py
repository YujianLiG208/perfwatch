from __future__ import annotations

from typing import Any

MOCK_TIMESTAMP_MS = 1710000000000


def get_mock_snapshot() -> dict[str, Any]:
    return {
        "timestamp_ms": MOCK_TIMESTAMP_MS,
        "cpu": {
            "usage_percent": 42.5,
            "frequency_mhz": 3600.0,
            "package_power_watts": 35.0,
            "temperature_celsius": 65.0,
        },
        "memory": {
            "total_bytes": 34359738368,
            "used_bytes": 17179869184,
        },
        "battery": {
            "available": True,
            "charging": False,
            "percent": 78.0,
            "power_watts": 18.5,
            "energy_remaining_wh": 45.0,
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
                "cpu_percent": 12.5,
                "rss_bytes": 268435456,
                "vram_bytes": 0,
                "estimated_power_score": 0.42,
            }
        ],
    }


class MockCollector:
    def collect(self) -> dict[str, Any]:
        return get_mock_snapshot()
