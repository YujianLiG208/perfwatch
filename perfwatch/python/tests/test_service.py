import asyncio
from copy import deepcopy
import sqlite3

from perfwatch.api.service import ServiceState
from perfwatch.collectors.mock import get_mock_snapshot
from perfwatch.config.settings import Settings
from perfwatch.storage.repository import SnapshotRepository


class CountingCollector:
    def __init__(self) -> None:
        self.count = 0

    def collect(self) -> dict:
        self.count += 1
        snapshot = deepcopy(get_mock_snapshot())
        snapshot["timestamp_ms"] += self.count
        return snapshot


class FailingCollector:
    def collect(self) -> dict:
        raise RuntimeError("collector unavailable")


class TrackingRepository(SnapshotRepository):
    def __init__(self, database_path) -> None:
        super().__init__(database_path)
        self.closed = False

    def close(self) -> None:
        self.closed = True
        super().close()


def test_service_startup_starts_sampling_task(tmp_path) -> None:
    async def exercise() -> None:
        service = ServiceState(
            settings=Settings(
                database_path=tmp_path / "startup.sqlite3",
                snapshot_interval_seconds=0.01,
                use_mock_collector=True,
            ),
            collector=CountingCollector(),
            repository=SnapshotRepository(tmp_path / "startup.sqlite3"),
        )

        await service.start()
        try:
            assert service.current_snapshot is not None
            assert service.sampling_task is not None
            assert not service.sampling_task.done()
        finally:
            await service.stop()

    asyncio.run(exercise())


def test_service_shutdown_stops_task_and_closes_repository(tmp_path) -> None:
    async def exercise() -> None:
        repository = TrackingRepository(tmp_path / "shutdown.sqlite3")
        service = ServiceState(
            settings=Settings(
                database_path=tmp_path / "shutdown.sqlite3",
                snapshot_interval_seconds=0.01,
                use_mock_collector=True,
            ),
            collector=CountingCollector(),
            repository=repository,
        )

        await service.start()
        task = service.sampling_task
        await service.stop()

        assert task is not None
        assert task.done()
        assert service.sampling_task is None
        assert repository.closed

    asyncio.run(exercise())


def test_sampling_loop_updates_snapshot_and_writes_sqlite(tmp_path) -> None:
    database_path = tmp_path / "sampling.sqlite3"
    collector = CountingCollector()

    async def exercise() -> None:
        service = ServiceState(
            settings=Settings(
                database_path=database_path,
                snapshot_interval_seconds=0.01,
                use_mock_collector=True,
            ),
            collector=collector,
            repository=SnapshotRepository(database_path),
        )

        await service.start()
        await asyncio.sleep(0.04)
        await service.stop()

        assert collector.count >= 2
        assert service.current_snapshot is not None
        assert service.current_snapshot["timestamp_ms"] == 1710000000000 + collector.count

    asyncio.run(exercise())

    with sqlite3.connect(database_path) as connection:
        sample_count = connection.execute("SELECT COUNT(*) FROM samples_system").fetchone()[0]

    assert sample_count == collector.count


def test_collector_errors_are_recorded_without_stopping_service(tmp_path) -> None:
    database_path = tmp_path / "errors.sqlite3"

    async def exercise() -> None:
        service = ServiceState(
            settings=Settings(
                database_path=database_path,
                snapshot_interval_seconds=0.01,
                use_mock_collector=True,
            ),
            collector=FailingCollector(),
            repository=SnapshotRepository(database_path),
        )

        await service.start()
        await asyncio.sleep(0.025)
        assert service.sampling_task is not None
        assert not service.sampling_task.done()
        await service.stop()

        assert service.current_snapshot is None

    asyncio.run(exercise())

    with sqlite3.connect(database_path) as connection:
        event = connection.execute(
            "SELECT level, source, message FROM events ORDER BY id LIMIT 1"
        ).fetchone()
        sample_count = connection.execute("SELECT COUNT(*) FROM samples_system").fetchone()[0]

    assert event is not None
    assert event[0] == "error"
    assert event[1] == "collector"
    assert "collector unavailable" in event[2]
    assert sample_count == 0
