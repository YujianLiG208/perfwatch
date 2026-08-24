# perfwatch

perfwatch is a Windows-first local performance and energy monitoring prototype. It combines a C++
collection layer, Python orchestration and persistence, a FastAPI service, and a React dashboard.

## Current Status

Phases 1-7 are complete and form the current integrated, mock-driven application baseline.

| Phase | Status | Implemented scope |
| --- | --- | --- |
| 1 | Completed | Project skeleton, deterministic mock pipeline, Python/C++ boundaries, CI, and development setup. |
| 2 | Completed | Fixture-tested parsers for Linux `/proc/stat`, `/proc/meminfo`, `/proc/<pid>/stat`, and battery `uevent` data. |
| 3 | Completed | Hardened SQLite writes, batch insertion, events, recent-sample queries, indexes, and retention cleanup. |
| 4 | Completed | Background sampling loop, SQLite persistence, API history/process queries, WebSocket streaming, configuration, and graceful shutdown. |
| 5 | Completed | Vite/React/TypeScript dashboard with current metrics, history charts, top processes, WebSocket updates, and HTTP fallback. |
| 6 | Completed | Root GitHub Actions CI with Python/C++ validation on Windows and Ubuntu using Python 3.11 and 3.12, Node 24 frontend test/build, Ruff, and stable required checks `python-cpp`, `frontend`, and `quality`. |
| 7 | Completed | Deterministic evolving mock samples, analytics enrichment and persistence, and one local production entry point serving the API and built Dashboard together. |

## Implemented Architecture

- **C++:** collector interfaces, deterministic evolving mock data, optional pybind11 bindings, and
  fixture-driven Linux parsers. The parsers do not read the live host filesystem.
- **Python:** mock/native-compatible collection, battery-runtime and process-energy enrichment,
  SQLite storage, service orchestration, and the `perfwatch-server` production entry point.
- **API:** `GET /health`, `GET /snapshot`, `GET /metrics/recent`, `GET /processes/top`, and
  `WebSocket /ws/snapshot` in the integrated baseline.
- **Dashboard:** local CPU, memory, battery, package-power, process, history, and connection views,
  served with same-origin HTTP and WebSocket paths in production.

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
| 8 | Implement live Windows collection, the transparent desktop overlay, and Windows production packaging and release artifacts. |
| 9 | Perform physical Windows hardware validation, browser and overlay visual validation, and a packaged full-flow acceptance run. |

Phase 9 is complete only when the packaged Windows application can collect, estimate, persist,
query, stream, display, overlay, shut down, and restart successfully on the available physical
Windows laptop. See [`docs/roadmap.md`](docs/roadmap.md) for detailed acceptance scope.

## Run Locally

Build the Dashboard and run the integrated local production application from the repository root:

```powershell
cd ui\dashboard
npm.cmd run build
cd ..\..
python -m pip install -e python
perfwatch-server --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. For a non-default build layout, pass the directory containing
`index.html` explicitly:

```powershell
perfwatch-server --dashboard-directory C:\path\to\dashboard\dist
```

For development with Vite hot reload, start the API and Dashboard separately.

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
- Battery-runtime and process-energy values remain estimates rather than measured watts.
- The evolving mock samples are deterministic fixtures, not live sensor readings.
- The transparent overlay and Windows packaging are deferred to Phase 8.
- Release publication remains deferred to Phase 8.
- Automated tests do not validate real hardware sensors or browser and overlay visuals; those
  checks are the Phase 9 acceptance work.
- Live Linux collection and GPU vendor adapters are long-term plans outside Phases 6-9.
