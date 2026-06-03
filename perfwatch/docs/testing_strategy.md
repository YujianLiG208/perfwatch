# Testing Strategy

## Unit Tests

Python unit tests cover deterministic mock collection, simple analytics helpers, SQLite insertion,
and API endpoints.

## Mock Tests

C++ and Python mock tests verify stable values and expected keys. This is the Phase 1 test anchor.

## Fixture Tests

Linux and Windows fixture directories are present for future parser work. No real parser behavior is
implemented yet.

## CI Limitations

CI can validate deterministic code paths and build shape. It cannot validate real hardware sensors.

## Future Real-Hardware Testing

Later phases should add opt-in local hardware tests that are excluded from default CI.
