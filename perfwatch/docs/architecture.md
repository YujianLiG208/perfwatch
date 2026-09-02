# Architecture

PerfWatch is one local Windows application with a native collector, Python service, SQLite database,
web Dashboard, and Win32 Overlay.

## Data flow

`WindowsCollector → enrichment → SQLiteWriter → HTTP/WebSocket → Dashboard and Overlay`

The explicit `--mock` path replaces only the collector and is used by tests and package smoke
checks. Native collector failures never silently select mock data.

## Native collector

`cpp/platform/windows/windows_collector.cpp` reads Windows CPU, memory, battery, and process data.
It keeps PDH and per-process CPU baselines in one collector instance and returns at most ten process
rows. Unsupported measurements use nullable fields. pybind11 exposes this collector to Python.

## Python service and storage

`ServiceState` owns the collector, latest snapshot, sampling task, and `SQLiteWriter`. Each sample is
enriched before it becomes current and is persisted. Stable collection capability warnings are
recorded once; collector, analytics, and storage errors do not terminate the loop.

SQLite stores system samples, process samples, and events. The writer supports the five operations
used by the application: initialize, add a snapshot, add an event, fetch recent metrics, and fetch
top processes. Schema initialization includes the one legacy battery-estimate migration.

FastAPI exposes:

- `GET /health`
- `GET /snapshot`
- `GET /metrics/recent`
- `GET /processes/top`
- `WebSocket /ws/snapshot`

## User interfaces

The React Dashboard loads current/history/process data over HTTP, receives live snapshots over the
WebSocket, and polls HTTP while reconnecting. It keeps a 60-sample chart window.

The native Overlay is a small topmost, translucent, click-through Win32 window. It polls the local
snapshot endpoint and displays waiting, live, or stale state. The packaged runtime starts Uvicorn
and the Overlay and coordinates their shutdown.

## Packaging

PyInstaller produces an unsigned directory bundle containing the executable, Dashboard, SQLite
schema, and native module. PowerShell creates a versioned ZIP and SHA-256 file. GitHub Actions can
build artifacts manually and publishes a GitHub Release only for an exact version tag.
