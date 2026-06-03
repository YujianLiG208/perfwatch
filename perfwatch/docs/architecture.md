# Architecture

## Native C++ Collector Layer

The C++ layer defines simple sample structs, a `Collector` interface, and a deterministic
`MockCollector`. Platform-specific files are compile-safe placeholders with TODO comments.

## Python Orchestration Layer

Python imports `perfwatch_native` when available and falls back to the Python mock collector when the
native module is not built. This keeps Phase 1 testable without real hardware access.

## SQLite Storage

SQLite stores system samples, process samples, and events. The schema uses `ts_ms` timestamps and
names estimated fields with `estimated` or `score`.

## FastAPI Service

The API exposes `/health` and `/snapshot`. A minimal WebSocket skeleton is present for future mock
streaming work.

## Future Dashboard Layer

`ui/dashboard` and `ui/overlay` are placeholders. No web UI or overlay is implemented in Phase 1.

## Mock and Fixture Testing Strategy

Phase 1 tests use deterministic mocks. Fixture files exist for later parser work without reading
host hardware.
