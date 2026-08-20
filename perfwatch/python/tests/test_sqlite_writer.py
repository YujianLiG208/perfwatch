import sqlite3
from copy import deepcopy

import pytest

from perfwatch.collectors.mock import get_mock_snapshot
from perfwatch.storage.sqlite_writer import SQLiteWriter


def snapshot_at(timestamp_ms: int, process_name: str = "mock_process") -> dict:
    snapshot = deepcopy(get_mock_snapshot())
    snapshot["timestamp_ms"] = timestamp_ms
    snapshot["top_processes"][0]["name"] = process_name
    return snapshot


def test_sqlite_writer_initializes_schema(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)

    writer.initialize()

    with sqlite3.connect(database_path) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        index_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }

    assert {"samples_system", "samples_process", "events"} <= table_names
    assert {
        "idx_samples_system_ts_ms",
        "idx_samples_process_ts_ms",
        "idx_events_ts_ms",
    } <= index_names


def test_sqlite_writer_inserts_single_snapshot(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)

    system_id = writer.insert_snapshot(get_mock_snapshot())

    assert system_id == 1
    with sqlite3.connect(database_path) as connection:
        system_row = connection.execute(
            "SELECT ts_ms, cpu_usage_percent, battery_available FROM samples_system"
        ).fetchone()
        process_row = connection.execute(
            "SELECT name, estimated_power_score FROM samples_process"
        ).fetchone()

    assert system_row == (1710000000000, 42.5, 1)
    assert process_row == ("mock_process", 0.42)


def test_sqlite_writer_inserts_snapshot_batch(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)

    system_ids = writer.insert_snapshots(
        [
            snapshot_at(1710000000000, "first_process"),
            snapshot_at(1710000001000, "second_process"),
        ]
    )

    assert system_ids == [1, 2]
    with sqlite3.connect(database_path) as connection:
        system_count = connection.execute("SELECT COUNT(*) FROM samples_system").fetchone()[0]
        process_names = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM samples_process ORDER BY ts_ms"
            ).fetchall()
        ]

    assert system_count == 2
    assert process_names == ["first_process", "second_process"]


def test_sqlite_writer_rolls_back_snapshot_batch_on_invalid_process(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)
    valid = snapshot_at(1000, "valid")
    invalid = snapshot_at(2000, "invalid")
    invalid["top_processes"][0]["rss_bytes"] = "not-an-integer"

    with pytest.raises(ValueError):
        writer.insert_snapshots([valid, invalid])

    with sqlite3.connect(database_path) as connection:
        system_count = connection.execute("SELECT COUNT(*) FROM samples_system").fetchone()[0]
        process_count = connection.execute("SELECT COUNT(*) FROM samples_process").fetchone()[0]

    assert system_count == 0
    assert process_count == 0


def test_sqlite_writer_fetches_dashboard_metrics_and_top_processes(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)
    writer.insert_snapshots(
        [
            snapshot_at(1000, "old"),
            snapshot_at(2000, "latest"),
        ]
    )

    metrics = writer.fetch_recent_metrics(limit=1)
    processes = writer.fetch_top_processes(limit=1)

    assert [metric["timestamp_ms"] for metric in metrics] == [2000]
    assert metrics[0]["cpu"]["usage_percent"] == 42.5
    assert [process["name"] for process in processes] == ["latest"]


def test_sqlite_writer_inserts_process_samples(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)

    inserted = writer.insert_process_samples(
        1710000000000,
        [
            {
                "pid": 1234,
                "name": "app",
                "cpu_percent": 10.0,
                "rss_bytes": 1024,
                "vram_bytes": 0,
                "estimated_power_score": 0.5,
            },
            {
                "pid": 5678,
                "name": "worker",
                "cpu_percent": 4.0,
                "rss_bytes": 2048,
                "vram_bytes": 128,
                "estimated_power_score": 0.25,
            },
        ],
    )

    assert inserted == 2
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT pid, name, estimated_power_score FROM samples_process ORDER BY pid"
        ).fetchall()

    assert rows == [(1234, "app", 0.5), (5678, "worker", 0.25)]


def test_sqlite_writer_inserts_event(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)

    event_id = writer.insert_event(
        1710000000000,
        "warning",
        "storage",
        "snapshot contained unavailable battery fields",
    )

    assert event_id == 1
    with sqlite3.connect(database_path) as connection:
        row = connection.execute("SELECT ts_ms, level, source, message FROM events").fetchone()

    assert row == (
        1710000000000,
        "warning",
        "storage",
        "snapshot contained unavailable battery fields",
    )


def test_sqlite_writer_queries_recent_system_samples_by_time_window(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)
    writer.insert_snapshots(
        [
            snapshot_at(1000),
            snapshot_at(2000),
            snapshot_at(3000),
        ]
    )

    rows = writer.query_recent_system_samples(1500, 3000)

    assert [row["timestamp_ms"] for row in rows] == [3000, 2000]
    assert rows[0]["cpu_usage_percent"] == 42.5


def test_sqlite_writer_queries_recent_process_samples_by_time_window(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)
    writer.insert_snapshots(
        [
            snapshot_at(1000, "old"),
            snapshot_at(2000, "middle"),
            snapshot_at(3000, "new"),
        ]
    )

    rows = writer.query_recent_process_samples(1500, 3000, limit=1)

    assert [row["timestamp_ms"] for row in rows] == [3000]
    assert [row["name"] for row in rows] == ["new"]
    assert rows[0]["estimated_power_score"] == 0.42


def test_sqlite_writer_applies_retention_policy(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)
    writer.insert_snapshots(
        [
            snapshot_at(1000, "old"),
            snapshot_at(2000, "kept"),
        ]
    )
    writer.insert_event(1000, "error", "storage", "old event")
    writer.insert_event(2500, "warning", "storage", "kept event")

    deleted = writer.apply_retention_policy(2000)

    assert deleted == {
        "samples_system": 1,
        "samples_process": 1,
        "events": 1,
    }
    with sqlite3.connect(database_path) as connection:
        remaining_system = connection.execute("SELECT ts_ms FROM samples_system").fetchall()
        remaining_process = connection.execute("SELECT ts_ms FROM samples_process").fetchall()
        remaining_events = connection.execute("SELECT ts_ms FROM events ORDER BY ts_ms").fetchall()

    assert remaining_system == [(2000,)]
    assert remaining_process == [(2000,)]
    assert remaining_events == [(2500,)]


def test_sqlite_writer_handles_missing_optional_values(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)
    snapshot = snapshot_at(1710000000000)
    del snapshot["cpu"]["package_power_watts"]
    del snapshot["battery"]["charging"]
    snapshot.pop("gpu")
    snapshot["top_processes"] = [{"pid": 1234, "name": "partial_process"}]

    writer.insert_snapshot(snapshot)

    with sqlite3.connect(database_path) as connection:
        system_row = connection.execute(
            """
            SELECT cpu_package_power_watts, battery_charging, gpu_available
            FROM samples_system
            """
        ).fetchone()
        process_row = connection.execute(
            """
            SELECT pid, name, rss_bytes, estimated_power_score
            FROM samples_process
            """
        ).fetchone()

    assert system_row == (None, None, None)
    assert process_row == (1234, "partial_process", None, None)
