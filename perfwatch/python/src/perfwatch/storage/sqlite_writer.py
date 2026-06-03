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
