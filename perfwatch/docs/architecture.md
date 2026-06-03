# Architecture

## Native C++ Collector Layer

The C++ layer defines simple sample structs, a `Collector` interface, and a deterministic
`MockCollector`.

Phase 2 implements a focused Linux parser layer for fixture-tested system file formats:
`/proc/stat`, `/proc/meminfo`, `/proc/<pid>/stat`, and
`/sys/class/power_supply/BAT*/uevent`. These parsers accept strings or file contents and return
structured C++ data. They do not read the host `/proc` or `/sys` filesystem and are not yet wired
into real runtime Linux collection.

Windows collector and GPU files remain compile-safe placeholders for later phases.

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

Phase 1 tests use deterministic mocks. Phase 2 adds Linux parser fixture tests without reading host
hardware or live operating-system files.
