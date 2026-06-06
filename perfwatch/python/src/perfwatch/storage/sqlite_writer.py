from __future__ import annotations

import sqlite3
from importlib.resources import files
from pathlib import Path
from typing import Any


class SQLiteWriter:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def initialize(self) -> None:
        schema = files("perfwatch.storage").joinpath("schema.sql").read_text(encoding="utf-8")
        with self.connect() as connection:
            connection.executescript(schema)

    def insert_snapshot(self, snapshot: dict[str, Any]) -> int:
        self.initialize()
        ts_ms = int(snapshot["timestamp_ms"])
        cpu = snapshot["cpu"]
        memory = snapshot["memory"]
        battery = snapshot["battery"]
        gpu = snapshot["gpu"]
        processes = snapshot.get("top_processes", [])

        with self.connect() as connection:
            with connection:
                cursor = connection.execute(
                    """
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
                    """,
                    (
                        ts_ms,
                        cpu["usage_percent"],
                        cpu["frequency_mhz"],
                        cpu["package_power_watts"],
                        cpu["temperature_celsius"],
                        memory["total_bytes"],
                        memory["used_bytes"],
                        int(battery["available"]),
                        int(battery["charging"]),
                        battery["percent"],
                        battery["power_watts"],
                        battery["energy_remaining_wh"],
                        int(gpu["available"]),
                        gpu["vendor"],
                        gpu["usage_percent"],
                        gpu["vram_total_bytes"],
                        gpu["vram_used_bytes"],
                        gpu["power_watts"],
                        gpu["temperature_celsius"],
                    ),
                )
                if cursor.lastrowid is None:
                    raise RuntimeError("SQLite did not return a system sample id")
                system_id = int(cursor.lastrowid)

                connection.executemany(
                    """
                    INSERT INTO samples_process (
                        ts_ms,
                        pid,
                        name,
                        cpu_percent,
                        rss_bytes,
                        vram_bytes,
                        estimated_power_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            ts_ms,
                            process["pid"],
                            process["name"],
                            process["cpu_percent"],
                            process["rss_bytes"],
                            process["vram_bytes"],
                            process["estimated_power_score"],
                        )
                        for process in processes
                    ],
                )

        return system_id

    def insert_event(
        self,
        *,
        timestamp_ms: int,
        level: str,
        source: str,
        message: str,
    ) -> int:
        self.initialize()
        with self.connect() as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO events (ts_ms, level, source, message)
                    VALUES (?, ?, ?, ?)
                    """,
                    (timestamp_ms, level, source, message),
                )
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return an event id")
        return int(cursor.lastrowid)

    def fetch_recent_metrics(self, *, limit: int = 100) -> list[dict[str, Any]]:
        self.initialize()
        with self.connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT
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
        with self.connect() as connection:
            connection.row_factory = sqlite3.Row
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
                ) AS latest_process
                    ON latest_process.id = process.id
                ORDER BY
                    process.estimated_power_score DESC,
                    process.cpu_percent DESC,
                    process.id DESC
                LIMIT ?
                """,
                (timestamp_ms, limit),
            ).fetchall()

        return [dict(row) for row in rows]

    def close(self) -> None:
        # Connections are scoped to individual operations and committed before returning.
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
