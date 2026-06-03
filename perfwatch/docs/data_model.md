# Data Model

## samples_system

Stores one row per system snapshot using `ts_ms` as the timestamp. CPU, memory, battery, and GPU
fields are flattened for simple insertion and querying.

## samples_process

Stores per-process rows associated with a snapshot timestamp. `estimated_power_score` is a score,
not a measured watt value.

## events

Stores timestamped application events with level, source, and message fields.
