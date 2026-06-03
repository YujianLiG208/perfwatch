from __future__ import annotations


def estimate_remaining_seconds(
    energy_remaining_wh: float,
    discharge_power_w: float,
) -> float | None:
    if discharge_power_w <= 0:
        return None
    if energy_remaining_wh < 0:
        return None
    return energy_remaining_wh / discharge_power_w * 3600
