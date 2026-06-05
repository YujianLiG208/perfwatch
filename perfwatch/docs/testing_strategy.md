# Testing Strategy

## Unit Tests

Python unit tests cover deterministic mock collection, simple analytics helpers, SQLite insertion,
and API endpoints.

Phase 3 expands SQLite tests to cover schema initialization, single and batch snapshot insertion,
process sample insertion, event insertion, recent timestamp-window queries, retention cleanup, and
missing optional snapshot fields. These tests use `tmp_path` database files and do not create
permanent `.db`, `.sqlite`, or `.sqlite3` files in the repository.

## Mock Tests

C++ and Python mock tests verify stable values and expected keys. This is the Phase 1 test anchor.

## Fixture Tests

Phase 2 adds fixture-backed C++ tests for Linux parser behavior. The `/proc/stat`, `/proc/meminfo`,
`/proc/<pid>/stat`, and `/sys/class/power_supply/BAT*/uevent` parsers consume fixture strings and
files from `tests/fixtures/linux` instead of reading the host `/proc` or `/sys` filesystem.

Windows fixtures remain placeholders for later collector work.

## CI Limitations

CI can validate deterministic parser and mock code paths plus build shape. It cannot validate real
hardware sensors or runtime Linux collection. Phase 3 does not add real runtime collection.

## Future Real-Hardware Testing

Later phases should add opt-in local hardware tests that are excluded from default CI.
