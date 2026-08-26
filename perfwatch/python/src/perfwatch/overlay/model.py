from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Any, Literal


@dataclass(frozen=True)
class OverlayModel:
    lines: tuple[str, ...]
    status: Literal["waiting", "live", "stale"]


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if isfinite(number) else None


def _percent(value: object) -> str:
    number = _number(value)
    return "N/A" if number is None else f"{number:.1f}%"


def _bytes(value: object) -> str:
    number = _number(value)
    return "N/A" if number is None or number < 0 else f"{number / 2**30:.1f} GiB"


def _watts(value: object) -> str:
    number = _number(value)
    return "N/A" if number is None else f"{number:.1f} W"


def _frequency(value: object) -> str:
    number = _number(value)
    return "N/A" if number is None else f"{number:.0f} MHz"


def _duration(value: object) -> str:
    seconds = _number(value)
    if seconds is None or seconds < 0:
        return "N/A"
    hours, remainder = divmod(int(seconds), 3600)
    minutes = remainder // 60
    return f"{hours}h {minutes:02d}m" if hours else f"{minutes}m"


def _section(snapshot: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = snapshot.get(name)
    return value if isinstance(value, Mapping) else {}


def model_from_snapshot(snapshot: Mapping[str, Any]) -> OverlayModel:
    cpu = _section(snapshot, "cpu")
    memory = _section(snapshot, "memory")
    battery = _section(snapshot, "battery")
    processes = snapshot.get("top_processes")
    process = processes[0] if isinstance(processes, list) and processes else {}
    if not isinstance(process, Mapping):
        process = {}
    process_name = process.get("name")
    if not isinstance(process_name, str) or not process_name:
        process_name = "N/A"

    return OverlayModel(
        lines=(
            f"CPU {_percent(cpu.get('usage_percent'))}  {_frequency(cpu.get('frequency_mhz'))}",
            f"Memory {_bytes(memory.get('used_bytes'))} / {_bytes(memory.get('total_bytes'))}",
            (
                f"Battery {_percent(battery.get('percent'))}  "
                f"Remaining {_duration(battery.get('estimated_remaining_seconds'))}"
            ),
            (
                f"Power {_watts(cpu.get('package_power_watts'))} CPU  "
                f"{_watts(battery.get('power_watts'))} battery"
            ),
            f"Top {process_name}  CPU {_percent(process.get('cpu_percent'))}",
            "LIVE",
        ),
        status="live",
    )


def stale_model(previous: OverlayModel | None) -> OverlayModel:
    if previous is None or previous.status == "waiting":
        return OverlayModel(("Waiting for service",), "waiting")
    return OverlayModel((*previous.lines[:-1], "STALE"), "stale")
