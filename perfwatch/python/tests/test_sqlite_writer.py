import sqlite3

from perfwatch.collectors.mock import get_mock_snapshot
from perfwatch.storage.sqlite_writer import SQLiteWriter


def test_sqlite_writer_initializes_schema_and_inserts_snapshot(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)

    system_id = writer.insert_snapshot(get_mock_snapshot())

    assert system_id == 1
    with sqlite3.connect(database_path) as connection:
        system_count = connection.execute("SELECT COUNT(*) FROM samples_system").fetchone()[0]
        process_count = connection.execute("SELECT COUNT(*) FROM samples_process").fetchone()[0]

    assert system_count == 1
    assert process_count == 1
