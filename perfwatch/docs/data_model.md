# Data Model

SQLite (`SQLiteWriter`) persists system snapshots, top-process samples, and application events.
All unavailable sensor metrics and derived estimates without valid inputs are stored as `NULL`
(never zero-filled or mocked).

## Tables

- **`samples_system`**: One row per snapshot timestamp (`ts_ms`). Stores flattened CPU (usage,
  frequency, package power, temperature), memory, and battery (percentage, energy, rate,
  `battery_estimated_remaining_seconds REAL`) columns.
  - `battery_estimated_remaining_seconds` is populated only when the battery is discharging with
    non-negative energy and positive power.
  - `SQLiteWriter.initialize()` checks `PRAGMA table_info(samples_system)` and runs an idempotent
    `ALTER TABLE` migration if `battery_estimated_remaining_seconds` is missing.
- **`samples_process`**: Per-process rows indexed by snapshot timestamp (`ts_ms`) for latest
  top-process queries. Stores PID, process name, CPU usage, RSS memory, and the derived relative
  power score (`estimated_power_score`).
- **`events`**: Timestamped application events (`ts_ms`, `level`, `source`, `message`). Before a
  snapshot is persisted or published, any internal `_collection_issues` key from the native
  collector is stripped and each unique issue code is recorded once as an event.
