from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping
from contextlib import closing
from importlib.resources import files
from pathlib import Path
from typing import Any


SYSTEM_INSERT_SQL = """
INSERT INTO samples_system (
    ts_ms,
    cpu_usage_percent,
    cpu_frequency_mhz,
    cpu_package_power_watts,
    cpu_temperature_celsius,
    memory_total_bytes,
    memory_used_bytes,
    battery_available,
    battery_charging,
    battery_percent,
    battery_power_watts,
    battery_energy_remaining_wh,
    gpu_available,
    gpu_vendor,
    gpu_usage_percent,
    gpu_vram_total_bytes,
    gpu_vram_used_bytes,
    gpu_power_watts,
    gpu_temperature_celsius
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

PROCESS_INSERT_SQL = """
INSERT INTO samples_process (
    ts_ms,
    pid,
    name,
    cpu_percent,
    rss_bytes,
    vram_bytes,
    estimated_power_score
) VALUES (?, ?, ?, ?, ?, ?, ?)
"""


class SQLiteWriter:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def connect(self) -> sqlite3.Connection:
        self._ensure_parent_directory()
        connection = sqlite3.connect(self.database_path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        schema = files("perfwatch.storage").joinpath("schema.sql").read_text(encoding="utf-8")
        with closing(self.connect()) as connection:
            with connection:
                connection.executescript(schema)

    def insert_snapshot(self, snapshot: dict[str, Any]) -> int:
        system_ids = self.insert_snapshots([snapshot])
        return system_ids[0]

    def insert_snapshots(self, snapshots: Iterable[Mapping[str, Any]]) -> list[int]:
        snapshots = list(snapshots)
        self.initialize()

        if not snapshots:
            return []

        with closing(self.connect()) as connection:
            with connection:
                system_ids: list[int] = []
                for snapshot in snapshots:
                    ts_ms = _snapshot_timestamp(snapshot)
                    cursor = connection.execute(SYSTEM_INSERT_SQL, _system_values(snapshot, ts_ms))
                    system_ids.append(int(cursor.lastrowid))
                    self._insert_process_samples(
                        connection,
                        ts_ms,
                        _processes_from_snapshot(snapshot),
                    )

        return system_ids

    def insert_process_samples(
        self,
        timestamp_ms: int,
        processes: Iterable[Mapping[str, Any]],
    ) -> int:
        self.initialize()
        process_rows = list(processes)

        if not process_rows:
            return 0

        with closing(self.connect()) as connection:
            with connection:
                return self._insert_process_samples(connection, int(timestamp_ms), process_rows)

    def insert_event(self, timestamp_ms: int, level: str, source: str, message: str) -> int:
        if not level:
            raise ValueError("event level is required")
        if not source:
            raise ValueError("event source is required")
        if not message:
            raise ValueError("event message is required")

        self.initialize()

        with closing(self.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO events (ts_ms, level, source, message)
                    VALUES (?, ?, ?, ?)
                    """,
                    (int(timestamp_ms), level, source, message),
                )
                return int(cursor.lastrowid)

    def query_recent_system_samples(
        self,
        since_timestamp_ms: int,
        until_timestamp_ms: int | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        return self._query_recent(
            table="samples_system",
            since_timestamp_ms=since_timestamp_ms,
            until_timestamp_ms=until_timestamp_ms,
            limit=limit,
        )

    def query_recent_process_samples(
        self,
        since_timestamp_ms: int,
        until_timestamp_ms: int | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        return self._query_recent(
            table="samples_process",
            since_timestamp_ms=since_timestamp_ms,
            until_timestamp_ms=until_timestamp_ms,
            limit=limit,
        )

    def fetch_recent_metrics(self, *, limit: int = 100) -> list[dict[str, Any]]:
        self.initialize()
        with closing(self.connect()) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM samples_system
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._metric_from_row(row) for row in rows]

    def fetch_top_processes(
        self,
        *,
        limit: int = 10,
        timestamp_ms: int | None = None,
    ) -> list[dict[str, Any]]:
        self.initialize()
        with closing(self.connect()) as connection:
            if timestamp_ms is None:
                latest = connection.execute(
                    "SELECT ts_ms FROM samples_system ORDER BY id DESC LIMIT 1"
                ).fetchone()
                if latest is None:
                    return []
                timestamp_ms = int(latest["ts_ms"])

            rows = connection.execute(
                """
                SELECT
                    process.ts_ms,
                    process.pid,
                    process.name,
                    process.cpu_percent,
                    process.rss_bytes,
                    process.vram_bytes,
                    process.estimated_power_score
                FROM samples_process AS process
                INNER JOIN (
                    SELECT pid, MAX(id) AS id
                    FROM samples_process
                    WHERE ts_ms = ?
                    GROUP BY pid
                ) AS latest_process ON latest_process.id = process.id
                ORDER BY
                    process.estimated_power_score DESC,
                    process.cpu_percent DESC,
                    process.id DESC
                LIMIT ?
                """,
                (timestamp_ms, limit),
            ).fetchall()
        return [_row_to_public_dict(row) for row in rows]

    def apply_retention_policy(self, older_than_timestamp_ms: int) -> dict[str, int]:
        self.initialize()
        cutoff = int(older_than_timestamp_ms)
        deleted: dict[str, int] = {}

        with closing(self.connect()) as connection:
            with connection:
                for table in ("samples_system", "samples_process", "events"):
                    cursor = connection.execute(f"DELETE FROM {table} WHERE ts_ms < ?", (cutoff,))
                    deleted[table] = max(cursor.rowcount, 0)

        return deleted

    def close(self) -> None:
        return None

    @staticmethod
    def _metric_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "timestamp_ms": row["ts_ms"],
            "cpu": {
                "usage_percent": row["cpu_usage_percent"],
                "frequency_mhz": row["cpu_frequency_mhz"],
                "package_power_watts": row["cpu_package_power_watts"],
                "temperature_celsius": row["cpu_temperature_celsius"],
            },
            "memory": {
                "total_bytes": row["memory_total_bytes"],
                "used_bytes": row["memory_used_bytes"],
            },
            "battery": {
                "available": bool(row["battery_available"]),
                "charging": bool(row["battery_charging"]),
                "percent": row["battery_percent"],
                "power_watts": row["battery_power_watts"],
                "energy_remaining_wh": row["battery_energy_remaining_wh"],
            },
            "gpu": {
                "available": bool(row["gpu_available"]),
                "vendor": row["gpu_vendor"],
                "usage_percent": row["gpu_usage_percent"],
                "vram_total_bytes": row["gpu_vram_total_bytes"],
                "vram_used_bytes": row["gpu_vram_used_bytes"],
                "power_watts": row["gpu_power_watts"],
                "temperature_celsius": row["gpu_temperature_celsius"],
            },
        }

    def _query_recent(
        self,
        *,
        table: str,
        since_timestamp_ms: int,
        until_timestamp_ms: int | None,
        limit: int | None,
    ) -> list[dict[str, Any]]:
        if table not in {"samples_system", "samples_process"}:
            raise ValueError(f"unsupported sample table: {table}")
        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")

        self.initialize()

        params: list[Any] = [int(since_timestamp_ms)]
        where = "ts_ms >= ?"
        if until_timestamp_ms is not None:
            where += " AND ts_ms <= ?"
            params.append(int(until_timestamp_ms))

        sql = f"SELECT * FROM {table} WHERE {where} ORDER BY ts_ms DESC, id DESC"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(int(limit))

        with closing(self.connect()) as connection:
            rows = connection.execute(sql, params).fetchall()

        return [_row_to_public_dict(row) for row in rows]

    def _insert_process_samples(
        self,
        connection: sqlite3.Connection,
        timestamp_ms: int,
        processes: Iterable[Mapping[str, Any]],
    ) -> int:
        process_values = [_process_values(timestamp_ms, process) for process in processes]
        connection.executemany(PROCESS_INSERT_SQL, process_values)
        return len(process_values)

    def _ensure_parent_directory(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


def _snapshot_timestamp(snapshot: Mapping[str, Any]) -> int:
    try:
        return int(snapshot["timestamp_ms"])
    except KeyError as exc:
        raise ValueError("snapshot is missing required timestamp_ms") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError("snapshot timestamp_ms must be an integer") from exc


def _system_values(snapshot: Mapping[str, Any], timestamp_ms: int) -> tuple[Any, ...]:
    cpu = _section(snapshot, "cpu")
    memory = _section(snapshot, "memory")
    battery = _section(snapshot, "battery")
    gpu = _section(snapshot, "gpu")

    return (
        timestamp_ms,
        _as_float(cpu.get("usage_percent")),
        _as_float(cpu.get("frequency_mhz")),
        _as_float(cpu.get("package_power_watts")),
        _as_float(cpu.get("temperature_celsius")),
        _as_int(memory.get("total_bytes")),
        _as_int(memory.get("used_bytes")),
        _as_bool_int(battery.get("available")),
        _as_bool_int(battery.get("charging")),
        _as_float(battery.get("percent")),
        _as_float(battery.get("power_watts")),
        _as_float(battery.get("energy_remaining_wh")),
        _as_bool_int(gpu.get("available")),
        _as_text(gpu.get("vendor")),
        _as_float(gpu.get("usage_percent")),
        _as_int(gpu.get("vram_total_bytes")),
        _as_int(gpu.get("vram_used_bytes")),
        _as_float(gpu.get("power_watts")),
        _as_float(gpu.get("temperature_celsius")),
    )


def _processes_from_snapshot(snapshot: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    processes = snapshot.get("top_processes") or []
    if isinstance(processes, (Mapping, str, bytes)):
        return []
    return [process for process in processes if isinstance(process, Mapping)]


def _process_values(timestamp_ms: int, process: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        timestamp_ms,
        _as_int(process.get("pid")),
        _as_text(process.get("name")),
        _as_float(process.get("cpu_percent")),
        _as_int(process.get("rss_bytes")),
        _as_int(process.get("vram_bytes")),
        _as_float(process.get("estimated_power_score")),
    )


def _section(snapshot: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = snapshot.get(name)
    if isinstance(value, Mapping):
        return value
    return {}


def _row_to_public_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["timestamp_ms"] = data.pop("ts_ms")
    return data


def _as_bool_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(bool(value))


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
