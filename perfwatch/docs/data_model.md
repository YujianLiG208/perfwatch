# Data Model

Phase 3 hardens the SQLite persistence layer for mock system snapshots, process samples, and
application events. It does not add real runtime collection.

## samples_system

Stores one row per system snapshot using `ts_ms` as the timestamp. CPU, memory, battery, and GPU
fields are flattened for simple insertion and querying. Missing optional fields are stored as
`NULL` so partially unavailable snapshot sections can still be persisted.

## samples_process

Stores per-process rows associated with a snapshot timestamp. `estimated_power_score` is a score,
not a measured watt value. Recent process queries use the timestamp window on `ts_ms`.

## events

Stores timestamped application events with level, source, and message fields.

## Retention

The SQLite writer can delete `samples_system`, `samples_process`, and `events` rows older than a
given timestamp. Tests use temporary database files only.
