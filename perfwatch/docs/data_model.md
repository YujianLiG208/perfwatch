# Data Model

Phase 3 hardens the SQLite persistence layer for mock system snapshots, process samples, and
application events. In the integrated baseline, this data supplies the Phase 4 service and Phase 5
dashboard. It does not add real runtime collection.

## samples_system

Stores one row per system snapshot using `ts_ms` as the timestamp. CPU, memory, battery, and GPU
fields are flattened for single or batch insertion and time-window querying. The timestamp index
supports recent-history lookups, and repository results can be shaped as the metric series consumed
by the dashboard. Missing optional fields are stored as `NULL` so partially unavailable snapshot
sections can still be persisted.

## samples_process

Stores per-process rows associated with a snapshot timestamp. `estimated_power_score` is a score,
not a measured watt value. The timestamp index supports recent process windows and latest
top-process queries.

## events

Stores timestamped application events with level, source, and message fields. Event writes share
the persistence layer used by service error reporting.

## Retention

The SQLite writer can delete `samples_system`, `samples_process`, and `events` rows older than a
given timestamp. Retention cleanup is explicit rather than an automatic background policy. Tests
use temporary database files only.
