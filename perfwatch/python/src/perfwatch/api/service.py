from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import time
from typing import Any

from perfwatch.analytics.snapshot import enrich_snapshot
from perfwatch.collectors import Collector
from perfwatch.config.settings import Settings
from perfwatch.storage.sqlite_writer import SQLiteWriter


@dataclass
class ServiceState:
    settings: Settings
    collector: Collector
    repository: SQLiteWriter
    current_snapshot: dict[str, Any] | None = None
    sampling_task: asyncio.Task[None] | None = None
    _stop_event: asyncio.Event | None = None
    _reported_collection_issues: set[str] = field(default_factory=set, init=False, repr=False)

    async def start(self) -> None:
        if self.sampling_task is not None and not self.sampling_task.done():
            return

        self.repository.initialize()
        self._stop_event = asyncio.Event()
        await self.sample_once()
        self.sampling_task = asyncio.create_task(
            self._sampling_loop(),
            name="perfwatch-sampling-loop",
        )

    async def stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()

        task = self.sampling_task
        if task is not None:
            await task

        self.sampling_task = None
        self._stop_event = None

    async def sample_once(self) -> None:
        try:
            snapshot = self.collector.collect()
        except Exception as error:
            self._record_error(source="collector", error=error)
            return

        collection_issues = snapshot.pop("_collection_issues", [])
        if isinstance(collection_issues, list):
            for issue in collection_issues:
                if not isinstance(issue, dict):
                    continue
                code = issue.get("code")
                message = issue.get("message")
                if (
                    not isinstance(code, str)
                    or not code
                    or not isinstance(message, str)
                    or not message
                    or code in self._reported_collection_issues
                ):
                    continue
                try:
                    self.repository.add_event(
                        timestamp_ms=int(time.time() * 1000),
                        level="warning",
                        source="collector",
                        message=message,
                    )
                except Exception:
                    continue
                self._reported_collection_issues.add(code)

        try:
            enrich_snapshot(snapshot)
        except Exception as error:
            self._record_error(source="analytics", error=error)

        self.current_snapshot = snapshot
        try:
            self.repository.add_snapshot(snapshot)
        except Exception as error:
            self._record_error(source="storage", error=error)

    async def _sampling_loop(self) -> None:
        stop_event = self._stop_event
        if stop_event is None:
            return

        while not stop_event.is_set():
            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=self.settings.snapshot_interval_seconds,
                )
            except TimeoutError:
                await self.sample_once()

    def _record_error(self, *, source: str, error: Exception) -> None:
        try:
            self.repository.add_event(
                timestamp_ms=int(time.time() * 1000),
                level="error",
                source=source,
                message=f"{type(error).__name__}: {error}",
            )
        except Exception:
            pass
