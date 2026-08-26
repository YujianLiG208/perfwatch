# Architecture

The Phase 8 Windows application combines explicit mock or native collection, analytics enrichment,
SQLite persistence, FastAPI HTTP/WebSocket endpoints, the React Dashboard, a native Win32 Overlay,
and one packaged runtime.

## Native C++ Collector Layer

The C++ layer defines simple sample structs, a `Collector` interface, and a deterministic evolving
`MockCollector`. Each collector instance advances an independent sample index while index zero
preserves the original baseline values.

Phase 2 implements a focused Linux parser layer for fixture-tested system file formats:
`/proc/stat`, `/proc/meminfo`, `/proc/<pid>/stat`, and
`/sys/class/power_supply/BAT*/uevent`. These parsers accept strings or file contents and return
structured C++ data. They do not read the host `/proc` or `/sys` filesystem and are not yet wired
into real runtime Linux collection.

`WindowsCollector` uses PDH and Windows APIs for CPU, memory, battery, and process data. It keeps
PDH state and per-process CPU baselines in the collector instance, identifies processes by PID plus
creation time, and returns at most ten process rows. CPU package power, temperature, process VRAM,
and other unsupported measurements remain nullable. Stable collection issues cross pybind11 through
the private `_collection_issues` key; no unavailable value is replaced with mock data.

GPU vendor collection remains a compile-safe future boundary. Live Linux collection is also
deferred; the existing Linux code remains fixture-driven.

## Python Orchestration Layer

Python selects the deterministic mock only when configuration or the packaged `--mock` option asks
for it explicitly. Otherwise `NativeCollector` requires the compiled Windows collector and raises if
it is unavailable. At the shared sampling boundary, `ServiceState` removes `_collection_issues`,
records each stable issue code once, enriches the public snapshot with estimated battery runtime and
per-process energy scores, and only then makes it current or persists it. Analytics failure is
recorded without discarding the raw sample.

## SQLite Storage

SQLite stores system samples, process samples, and events. The schema uses `ts_ms` timestamps,
indexes time-window lookups, and names estimated fields with `estimated` or `score`. The integrated
repository supports single and batch snapshot insertion, event writes, recent system and process
windows, dashboard-shaped metric history, top-process queries, and retention cleanup.

The nullable battery-runtime estimate is stored in `battery_estimated_remaining_seconds`. Existing
databases receive the column through an additive, idempotent `PRAGMA table_info` check followed by
`ALTER TABLE` only when the column is absent.

Phase 8 required no schema migration. Existing CPU, memory, battery, GPU, and process columns already
accept `NULL`, so partially available Windows snapshots follow the established storage contract.

## FastAPI Service

`ServiceState` owns the collector, repository, latest snapshot, stop signal, and background sampling
task. The Phase 8 data flow is:

`explicit mock or WindowsCollector → issue stripping/enrichment → SQLite → HTTP/WebSocket → React/Overlay`

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

## Windows Runtime and Package

`perfwatch.runtime` starts Uvicorn in one non-daemon thread and optionally launches the same
executable as a private Overlay child process. The console main thread owns shutdown; on Windows,
`SIGBREAK` enters the same `KeyboardInterrupt` cleanup path. Frozen Dashboard/schema/native resources
remain inside the PyInstaller directory bundle, while the default mutable database is stored under
`%LOCALAPPDATA%\PerfWatch`.

PyInstaller 6.22.2 produces `perfwatch.exe` plus `_internal`, README, and LICENSE. The versioned
Windows x64 ZIP contains that directory and has a matching SHA-256 file. No installer, service,
updater, or signing layer is present.

## Native Win32 Overlay

The Overlay uses only Python `ctypes`, User32/GDI, and the existing HTTP client. One daemon worker
fetches `/snapshot` and posts immutable display models to the UI message loop. The topmost layered
tool window is non-activating and returns `HTTRANSPARENT`; GDI painting stays on the UI thread.
Before the first response it reports waiting, and after a connection failure it preserves the last
real values while marking them stale. Missing measurements render as `N/A`.

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

The dashboard presents CPU, memory, battery, package-power, and process data. Nullable Windows values
render as unavailable, and estimated process energy scores remain explicitly labeled as relative
estimates.

## Mock and Fixture Testing Strategy

Tests use deterministic mocks and temporary SQLite databases for repeatable contracts. Phase 8 adds
one focused Windows delta/tracker check, nullable Python/UI checks, an Overlay model/window check, a
runtime resource boundary check, a packaged explicit-mock HTTP/shutdown smoke, and ZIP extraction/
hash verification.

The local live collector smoke proves API availability on one machine, not sensor accuracy or
long-running physical-hardware behavior. Those and all browser/Overlay visual checks remain Phase 9.
