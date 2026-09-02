import sqlite3
from copy import deepcopy
from importlib.resources import files

import pytest

from perfwatch.collectors.mock import get_mock_snapshot
from perfwatch.storage.sqlite_writer import SQLiteWriter


def test_sqlite_writer_migrates_legacy_schema_without_losing_rows(tmp_path) -> None:
    database_path = tmp_path / "legacy.sqlite3"
    schema = files("perfwatch.storage").joinpath("schema.sql").read_text(encoding="utf-8")
    legacy_schema = schema.replace("    battery_estimated_remaining_seconds REAL,\n", "")
    with sqlite3.connect(database_path) as connection:
        connection.executescript(legacy_schema)
        connection.execute("INSERT INTO samples_system (ts_ms) VALUES (?)", (1234,))

    SQLiteWriter(database_path).initialize()

    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(samples_system)").fetchall()
        }
        timestamps = connection.execute("SELECT ts_ms FROM samples_system").fetchall()
    assert "battery_estimated_remaining_seconds" in columns
    assert timestamps == [(1234,)]


def test_sqlite_writer_adds_and_queries_snapshot(tmp_path) -> None:
    writer = SQLiteWriter(tmp_path / "perfwatch.sqlite3")
    snapshot = deepcopy(get_mock_snapshot())
    snapshot["battery"]["estimated_remaining_seconds"] = 8_756.75

    assert writer.add_snapshot(snapshot) == 1

    metrics = writer.get_recent_metrics(limit=1)
    processes = writer.get_top_processes(limit=1, timestamp_ms=snapshot["timestamp_ms"])
    assert metrics[0]["battery"]["estimated_remaining_seconds"] == 8_756.75
    assert processes[0]["name"] == "mock_process"


def test_sqlite_writer_rolls_back_snapshot_when_process_is_invalid(tmp_path) -> None:
    database_path = tmp_path / "rollback.sqlite3"
    writer = SQLiteWriter(database_path)
    snapshot = deepcopy(get_mock_snapshot())
    snapshot["top_processes"][0]["rss_bytes"] = "invalid"

    with pytest.raises(ValueError):
        writer.add_snapshot(snapshot)

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM samples_system").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM samples_process").fetchone()[0] == 0


def test_sqlite_writer_adds_event(tmp_path) -> None:
    database_path = tmp_path / "events.sqlite3"
    writer = SQLiteWriter(database_path)

    assert writer.add_event(timestamp_ms=1234, level="error", source="collector", message="bad") == 1

    with sqlite3.connect(database_path) as connection:
        row = connection.execute("SELECT ts_ms, level, source, message FROM events").fetchone()
    assert row == (1234, "error", "collector", "bad")
