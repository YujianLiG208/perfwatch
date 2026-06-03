# Testing Strategy

## Unit Tests

Python unit tests cover deterministic mock collection, simple analytics helpers, SQLite insertion,
and API endpoints.

## Mock Tests

C++ and Python mock tests verify stable values and expected keys. This is the Phase 1 test anchor.

## Fixture Tests

Phase 2 adds fixture-backed C++ tests for Linux parser behavior. The `/proc/stat`, `/proc/meminfo`,
`/proc/<pid>/stat`, and `/sys/class/power_supply/BAT*/uevent` parsers consume fixture strings and
files from `tests/fixtures/linux` instead of reading the host `/proc` or `/sys` filesystem.

Windows fixtures remain placeholders for later collector work.

## CI Limitations

CI can validate deterministic parser and mock code paths plus build shape. It cannot validate real
hardware sensors or runtime Linux collection.

## Future Real-Hardware Testing

Later phases should add opt-in local hardware tests that are excluded from default CI.
