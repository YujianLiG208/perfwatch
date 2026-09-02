# Data Model

SQLite persists enriched mock or live Windows system snapshots, process samples, and application
events for the integrated service, Dashboard, and Overlay.

## samples_system

Stores one row per system snapshot using `ts_ms` as the timestamp. CPU, memory, battery, and GPU
fields are flattened for insertion and recent-history lookup. Missing optional fields are stored as
`NULL` so partially unavailable snapshot sections can still be persisted.

Phase 8 keeps Windows CPU usage, frequency, package power, temperature, memory, battery percentage,
battery energy/rate, and related GPU fields nullable through C++ optionals, Python `None`, SQLite
`NULL`, and API/TypeScript `null`. Generic Windows collection does not fabricate unavailable package
power, temperature, process VRAM, or derived values. No Phase 8 schema migration was needed because
the existing metric columns already accept `NULL`.

`battery.estimated_remaining_seconds` is a `number | null` API field and is stored in the nullable
`battery_estimated_remaining_seconds REAL` column. It is populated only for available, discharging
batteries with valid non-negative energy and positive power. `SQLiteWriter.initialize()` reads
`PRAGMA table_info(samples_system)` and conditionally executes an additive `ALTER TABLE` migration,
so upgrading an existing database is idempotent and preserves legacy rows.

## samples_process

Stores per-process rows associated with a snapshot timestamp.
`top_processes[].estimated_power_score` is recomputed at the shared sampling boundary and is a
`number | null`; it is a relative score, not a measured watt value. Invalid or incomplete source
values produce `NULL` without removing the process. The timestamp index supports latest top-process
queries.

Live Windows rows populate the available PID, name, CPU, and RSS values. Process VRAM and the derived
score remain `NULL` when their inputs are unavailable; failed collection never substitutes a mock or
zero-valued process row.

## events

Stores timestamped application events with level, source, and message fields. Event writes share
the persistence layer used by service error reporting. The private native `_collection_issues` key
is removed before snapshot persistence/publication, and each stable issue code is recorded once as
an event instead.
