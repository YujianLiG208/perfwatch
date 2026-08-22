# perfwatch

perfwatch is a Windows-first local performance and energy monitoring prototype. It combines a C++
collection layer, Python orchestration and persistence, a FastAPI service, and a React dashboard.

## Current Status

Phases 1-6 are complete and form the current mock-driven baseline.

| Phase | Status | Implemented scope |
| --- | --- | --- |
| 1 | Completed | Project skeleton, deterministic mock pipeline, Python/C++ boundaries, CI, and development setup. |
| 2 | Completed | Fixture-tested parsers for Linux `/proc/stat`, `/proc/meminfo`, `/proc/<pid>/stat`, and battery `uevent` data. |
| 3 | Completed | Hardened SQLite writes, batch insertion, events, recent-sample queries, indexes, and retention cleanup. |
| 4 | Completed | Background sampling loop, SQLite persistence, API history/process queries, WebSocket streaming, configuration, and graceful shutdown. |
| 5 | Completed | Vite/React/TypeScript dashboard with current metrics, history charts, top processes, WebSocket updates, and HTTP fallback. |
| 6 | Completed | Root GitHub Actions CI with Python/C++ validation on Windows and Ubuntu using Python 3.11 and 3.12, Node 24 frontend test/build, Ruff, and stable required checks `python-cpp`, `frontend`, and `quality`. |

## Implemented Architecture

- **C++:** collector interfaces, deterministic mock data, optional pybind11 bindings, and
  fixture-driven Linux parsers. The parsers do not read the live host filesystem.
- **Python:** mock/native-compatible collection, battery-runtime and process-energy estimation
  helpers, SQLite storage, and service orchestration. The estimation helpers are not yet connected
  to the sampling pipeline.
- **API:** `GET /health`, `GET /snapshot`, `GET /metrics/recent`, `GET /processes/top`, and
  `WebSocket /ws/snapshot` in the integrated baseline.
- **Dashboard:** local CPU, memory, battery, package-power, process, history, and connection views
  in the integrated baseline.

## Platform Direction

- Windows is the only near-term runtime, validation, and release target.
- Existing Linux parser and collector boundaries are retained only as a
  **Future long-term plan for Linux**. Live Linux collection is not assigned to Phases 6-9.
- Existing GPU interfaces and the unavailable fallback are retained only as a
  **Future Long-term plan for GPU adapter**. Vendor-specific GPU adapters are not assigned to
  Phases 6-9.
- Phase 9 full-function acceptance covers the planned Windows scope and excludes these explicitly
  deferred Linux and GPU-adapter items.

## Planned Implementation

| Phase | Planned scope |
| --- | --- |
| 7 | Connect the estimation helpers, make mock timestamps and values evolve deterministically, and add one production entry point for the API and dashboard. |
| 8 | Implement live Windows collection, the transparent desktop overlay, and Windows production packaging and release artifacts. |
| 9 | Perform physical Windows hardware validation, browser and overlay visual validation, and a packaged full-flow acceptance run. |

Phase 9 is complete only when the packaged Windows application can collect, estimate, persist,
query, stream, display, overlay, shut down, and restart successfully on the available physical
Windows laptop. See [`docs/roadmap.md`](docs/roadmap.md) for detailed acceptance scope.

## Run the Current Baseline Locally

Use the current `main` checkout. Until Phase 7, start the API and dashboard separately.

Set up and start the API:

```powershell
cd python
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
$env:PERFWATCH_USE_MOCK_COLLECTOR = "true"
.\.venv\Scripts\python.exe -m uvicorn perfwatch.api.app:app --reload
```

In another terminal, start the dashboard:

```powershell
cd ui\dashboard
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173`.

## Validation

Run Python and C++ tests from the repository root:

```powershell
python -m pytest python/tests
cmake -S cpp -B build
cmake --build build --config Debug
ctest --test-dir build --output-on-failure -C Debug
```

Validate the dashboard from the same integrated checkout:

```powershell
cd ui\dashboard
npm.cmd run test
npm.cmd run build
```

## Current Limitations

- The runtime still uses mock/native-compatible mock data; live Windows collection is planned for
  Phase 8.
- Battery-runtime and process-energy helpers are not connected to sampling, and their results will
  remain estimates rather than measured watts after Phase 7 integration.
- The built-in mock timestamp and values are fixed, so realistic evolving history is deferred to
  Phase 7.
- The API and dashboard require separate development processes until the Phase 7 production entry
  point is added.
- The transparent overlay and Windows packaging are deferred to Phase 8.
- Release publication remains deferred to Phase 8.
- Automated tests do not validate real hardware sensors or browser and overlay visuals; those
  checks are the Phase 9 acceptance work.
- Live Linux collection and GPU vendor adapters are long-term plans outside Phases 6-9.
