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

    def add_snapshots(self, snapshots: Iterable[Mapping[str, Any]]) -> list[int]:
        return self.writer.insert_snapshots(snapshots)

    def add_process_samples(
        self,
        timestamp_ms: int,
        processes: Iterable[Mapping[str, Any]],
    ) -> int:
        return self.writer.insert_process_samples(timestamp_ms, processes)

    def add_event(self, timestamp_ms: int, level: str, source: str, message: str) -> int:
        return self.writer.insert_event(timestamp_ms, level, source, message)

    def recent_system_samples(
        self,
        since_timestamp_ms: int,
        until_timestamp_ms: int | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.writer.query_recent_system_samples(
            since_timestamp_ms,
            until_timestamp_ms,
            limit,
        )

    def recent_process_samples(
        self,
        since_timestamp_ms: int,
        until_timestamp_ms: int | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.writer.query_recent_process_samples(
            since_timestamp_ms,
            until_timestamp_ms,
            limit,
        )

    def apply_retention_policy(self, older_than_timestamp_ms: int) -> dict[str, int]:
        return self.writer.apply_retention_policy(older_than_timestamp_ms)
