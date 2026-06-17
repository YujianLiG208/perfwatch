from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from perfwatch.storage.sqlite_writer import SQLiteWriter


class SnapshotRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.writer = SQLiteWriter(database_path)

    def add_snapshot(self, snapshot: dict[str, Any]) -> int:
        return self.writer.insert_snapshot(snapshot)

    def initialize(self) -> None:
        self.writer.initialize()

    def add_event(
        self,
        *,
        timestamp_ms: int,
        level: str,
        source: str,
        message: str,
    ) -> int:
        return self.writer.insert_event(
            timestamp_ms=timestamp_ms,
            level=level,
            source=source,
            message=message,
        )

    def get_recent_metrics(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.writer.fetch_recent_metrics(limit=limit)

    def get_top_processes(
        self,
        *,
        limit: int = 10,
        timestamp_ms: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.writer.fetch_top_processes(
            limit=limit,
            timestamp_ms=timestamp_ms,
        )

    def close(self) -> None:
        self.writer.close()
