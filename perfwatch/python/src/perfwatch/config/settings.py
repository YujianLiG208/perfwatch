from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("perfwatch.sqlite3")
    snapshot_interval_seconds: float = 1.0
    use_mock_collector: bool = False


def get_settings() -> Settings:
    interval = float(os.getenv("PERFWATCH_SAMPLE_INTERVAL_SECONDS", "1.0"))
    if interval <= 0:
        raise ValueError("PERFWATCH_SAMPLE_INTERVAL_SECONDS must be greater than zero")

    return Settings(
        database_path=Path(os.getenv("PERFWATCH_DATABASE_PATH", "perfwatch.sqlite3")),
        snapshot_interval_seconds=interval,
        use_mock_collector=_read_bool("PERFWATCH_USE_MOCK_COLLECTOR", default=False),
    )


def _read_bool(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")
