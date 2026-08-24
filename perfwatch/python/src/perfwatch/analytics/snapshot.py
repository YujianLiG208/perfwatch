from __future__ import annotations

from collections.abc import MutableMapping
from math import isfinite
from typing import Any

from perfwatch.analytics.battery_forecast import estimate_remaining_seconds
from perfwatch.analytics.process_energy_score import estimate_process_power_score


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if isfinite(number) else None


def _non_negative_int(value: object) -> int | None:
    number = _number(value)
    if number is None or number < 0 or not number.is_integer():
        return None
    return int(number)


def enrich_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    battery = snapshot.get("battery")
    if isinstance(battery, MutableMapping):
        energy = _number(battery.get("energy_remaining_wh"))
        power = _number(battery.get("power_watts"))
        battery["estimated_remaining_seconds"] = (
            estimate_remaining_seconds(energy, power)
            if battery.get("available") is True
            and battery.get("charging") is False
            and energy is not None
            and energy >= 0
            and power is not None
            and power > 0
            else None
        )

    processes = snapshot.get("top_processes")
    if isinstance(processes, list):
        for process in processes:
            if not isinstance(process, MutableMapping):
                continue
            cpu = _number(process.get("cpu_percent"))
            rss = _non_negative_int(process.get("rss_bytes"))
            vram = _non_negative_int(process.get("vram_bytes", 0))
            process["estimated_power_score"] = (
                estimate_process_power_score(cpu, rss, vram)
                if cpu is not None and cpu >= 0 and rss is not None and vram is not None
                else None
            )

    return snapshot
