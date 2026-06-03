from __future__ import annotations

from pathlib import Path
from typing import Any

from perfwatch.storage.sqlite_writer import SQLiteWriter


class SnapshotRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.writer = SQLiteWriter(database_path)

    def add_snapshot(self, snapshot: dict[str, Any]) -> int:
        return self.writer.insert_snapshot(snapshot)
