from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("perfwatch.sqlite3")
    snapshot_interval_seconds: float = 1.0


def get_settings() -> Settings:
    return Settings()
