# Architecture

The Phase 7 integrated application combines deterministic collection, analytics enrichment,
SQLite persistence, FastAPI HTTP/WebSocket endpoints, and the React Dashboard in one local flow.

## Native C++ Collector Layer

The C++ layer defines simple sample structs, a `Collector` interface, and a deterministic evolving
`MockCollector`. Each collector instance advances an independent sample index while index zero
preserves the original baseline values.

Phase 2 implements a focused Linux parser layer for fixture-tested system file formats:
`/proc/stat`, `/proc/meminfo`, `/proc/<pid>/stat`, and
`/sys/class/power_supply/BAT*/uevent`. These parsers accept strings or file contents and return
structured C++ data. They do not read the host `/proc` or `/sys` filesystem and are not yet wired
into real runtime Linux collection.

Windows collector and GPU files remain compile-safe placeholders for later phases.

## Python Orchestration Layer

Python imports `perfwatch_native` when available and falls back to the Python mock collector when the
native module is not built. Both paths use the same indexed sample contract. At the shared sampling
boundary, the service enriches each snapshot with an estimated battery runtime and recomputed
per-process energy scores before making it current or persisting it. Analytics failure is recorded
without discarding the raw sample. Neither collector path requires real hardware sensors.

## SQLite Storage

SQLite stores system samples, process samples, and events. The schema uses `ts_ms` timestamps,
indexes time-window lookups, and names estimated fields with `estimated` or `score`. The integrated
repository supports single and batch snapshot insertion, event writes, recent system and process
windows, dashboard-shaped metric history, top-process queries, and retention cleanup.

The nullable battery-runtime estimate is stored in `battery_estimated_remaining_seconds`. Existing
databases receive the column through an additive, idempotent `PRAGMA table_info` check followed by
`ALTER TABLE` only when the column is absent.

## FastAPI Service

`ServiceState` owns the collector, repository, latest snapshot, stop signal, and background sampling
task. The Phase 7 data flow is:

`collector → enrichment → current snapshot → SQLite → HTTP/WebSocket → React`

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

`create_app()` optionally mounts built Dashboard assets at `/` after every HTTP and WebSocket route,
so the static catch-all cannot shadow the API. `perfwatch-server` validates the selected Dashboard
directory and runs this combined application through Uvicorn. It does not build frontend assets.

The integrated baseline still does not add live Linux, Windows, or GPU collection, an overlay, or
packaging functionality.

## Web Dashboard Layer

The Vite, React, and TypeScript Dashboard under `ui/dashboard` uses the local API:

- initial data from `GET /health`, `GET /snapshot`, `GET /metrics/recent`, and
  `GET /processes/top`;
- live full-snapshot updates from `WebSocket /ws/snapshot`;
- HTTP polling every five seconds while WebSocket connectivity is unavailable;
- bounded WebSocket reconnect delays of 1, 2, 4, 8, and 10 seconds;
- a 60-sample in-memory chart window with timestamp sorting and de-duplication.

The development server proxies `/api/*` and `/ws/*` to the local FastAPI service. Production assets
use same-origin `/` HTTP paths and `/ws/snapshot`; `perfwatch-server` serves those assets and API
routes from one origin. React component state is sufficient for the MVP; no global state framework
is used.

The dashboard presents CPU, memory, battery, package-power, and process data. Estimated process
energy scores remain explicitly labeled as relative estimates. The overlay is still a placeholder.

## Mock and Fixture Testing Strategy

Tests use deterministic mocks and temporary SQLite databases. Phase 7 adds indexed Python/C++ mock
parity, enrichment and migration coverage, nullable Dashboard rendering, static/API/WebSocket route
coexistence, server CLI tests, production build validation, and an integrated TestClient smoke test.

These deterministic mocks and fixtures validate integration behavior, not physical sensors or
live operating-system collection.
