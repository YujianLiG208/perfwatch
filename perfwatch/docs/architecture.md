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
native module is not built. Phase 4 adds a minimal collector factory so the service can explicitly
use the Python mock collector or the native-compatible collector path. Neither path requires real
hardware sensors.

## SQLite Storage

SQLite stores system samples, process samples, and events. The schema uses `ts_ms` timestamps and
names estimated fields with `estimated` or `score`. The repository supports snapshot insertion,
recent system metric queries, latest top-process queries, and service error events.

## FastAPI Service

Phase 4 connects collection, SQLite persistence, and FastAPI through a `ServiceState` object. The
state owns the collector, repository, latest snapshot, stop signal, and background sampling task.

FastAPI lifespan startup initializes SQLite, takes an initial sample, and starts an asyncio sampling
loop. Each successful sample replaces the latest snapshot and is written to SQLite. Collector or
storage exceptions are recorded in the `events` table without terminating the loop. Lifespan
shutdown signals and awaits the task before closing the repository.

The local API exposes:

- `GET /health`
- `GET /snapshot`
- `GET /metrics/recent`
- `GET /processes/top`
- `WebSocket /ws/snapshot`

Configuration remains intentionally small:

- `PERFWATCH_SAMPLE_INTERVAL_SECONDS`, default `1.0`
- `PERFWATCH_DATABASE_PATH`, default `perfwatch.sqlite3`
- `PERFWATCH_USE_MOCK_COLLECTOR`, default `false`

This phase implements backend service orchestration only. It does not add real Linux, Windows, GPU,
dashboard, overlay, or packaging functionality.

## Web Dashboard Layer

Phase 5 implements a local Vite, React, and TypeScript dashboard under `ui/dashboard`. It uses the
existing Phase 4 API without changing backend response shapes:

- initial data from `GET /health`, `GET /snapshot`, `GET /metrics/recent`, and
  `GET /processes/top`;
- live full-snapshot updates from `WebSocket /ws/snapshot`;
- HTTP polling every five seconds while WebSocket connectivity is unavailable;
- bounded WebSocket reconnect delays of 1, 2, 4, 8, and 10 seconds;
- a 60-sample in-memory chart window with timestamp sorting and de-duplication.

The development server proxies `/api/*` and `/ws/*` to the local FastAPI service, so Phase 5 does
not require a CORS or API contract change. `VITE_API_BASE_URL` and `VITE_WS_URL` allow alternate
local integration URLs. React component state is sufficient for the MVP; no global state framework
is used.

The dashboard presents CPU, memory, battery, package-power, and process data. Estimated process
energy scores remain explicitly labeled as relative estimates. The overlay is still a placeholder.

## Mock and Fixture Testing Strategy

Phase 1 tests use deterministic mocks. Phase 2 adds Linux parser fixture tests without reading host
hardware or live operating-system files. Phase 4 service and API tests use the
mock/native-compatible collector interface and temporary SQLite databases. Phase 5 frontend tests
mock browser network boundaries while exercising the real data, connection, and component code.
