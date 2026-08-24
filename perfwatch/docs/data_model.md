# Data Model

SQLite persists enriched mock system snapshots, process samples, and application events for the
integrated service and Dashboard. It does not add real runtime collection.

## samples_system

Stores one row per system snapshot using `ts_ms` as the timestamp. CPU, memory, battery, and GPU
fields are flattened for single or batch insertion and time-window querying. The timestamp index
supports recent-history lookups, and repository results can be shaped as the metric series consumed
by the dashboard. Missing optional fields are stored as `NULL` so partially unavailable snapshot
sections can still be persisted.

`battery.estimated_remaining_seconds` is a `number | null` API field and is stored in the nullable
`battery_estimated_remaining_seconds REAL` column. It is populated only for available, discharging
batteries with valid non-negative energy and positive power. `SQLiteWriter.initialize()` reads
`PRAGMA table_info(samples_system)` and conditionally executes an additive `ALTER TABLE` migration,
so upgrading an existing database is idempotent and preserves legacy rows.

## samples_process

Stores per-process rows associated with a snapshot timestamp.
`top_processes[].estimated_power_score` is recomputed at the shared sampling boundary and is a
`number | null`; it is a relative score, not a measured watt value. Invalid or incomplete source
values produce `NULL` without removing the process. The timestamp index supports recent process
windows and latest top-process queries.

## events

Stores timestamped application events with level, source, and message fields. Event writes share
the persistence layer used by service error reporting.

## Retention

The SQLite writer can delete `samples_system`, `samples_process`, and `events` rows older than a
given timestamp. Retention cleanup is explicit rather than an automatic background policy. Tests
use temporary database files only.
