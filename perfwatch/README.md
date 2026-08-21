# perfwatch

perfwatch is a local performance and energy monitoring prototype. It combines a C++ collection
layer, Python orchestration and persistence, a FastAPI service, and a React dashboard.

## Current Status

Phase 3 persistence, the Phase 4 service loop, and the Phase 5 dashboard are
integrated on `codex/phase-3-5-integration`. `main` contains their separately
merged histories; the integration conflict-resolution and documentation commits
remain on the integration branch until its pull request is merged.

| Phase | Branch | Implemented scope |
| --- | --- | --- |
| 1 | `main` | Project skeleton, deterministic mock pipeline, Python/C++ boundaries, CI and development setup. |
| 2 | `main` | Fixture-tested parsers for Linux `/proc/stat`, `/proc/meminfo`, `/proc/<pid>/stat`, and battery `uevent` data. |
| 3 | `codex/phase-3-sqlite-persistence` | Hardened SQLite writes, batch insertion, events, recent-sample queries, indexes, and retention cleanup. |
| 4 | `codex/phase-4-service-loop` | Background sampling loop, SQLite persistence, API history/process queries, WebSocket streaming, configuration, and graceful shutdown. |
| 5 | `codex/phase-5` | Vite/React/TypeScript dashboard with current metrics, history charts, top processes, WebSocket updates, and HTTP fallback. |

The branch names above identify the historical source branches. The integration
branch combines their behavior into one baseline: the hardened Phase 3
writer/repository, the Phase 4 service/API, and the Phase 5 dashboard.

## Implemented Architecture

- **C++:** collector interfaces, deterministic mock data, optional pybind11 bindings, and
  fixture-driven Linux parsers. The parsers do not read the live host filesystem.
- **Python:** mock/native-compatible collection, simple battery and process-energy estimates,
  SQLite storage, and service orchestration.
- **API:** `GET /health`, `GET /snapshot`, `GET /metrics/recent`, `GET /processes/top`, and
  `WebSocket /ws/snapshot` in the integrated baseline.
- **Dashboard:** local CPU, memory, battery, package-power, process, history, and connection views
  in the integrated baseline.

## Run the Integrated Baseline Locally

Use the current `codex/phase-3-5-integration` checkout.

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

- Linux support is parser-only; live `/proc` and `/sys` collection is not wired into the runtime.
- Windows PDH/WMI collection, GPU adapters, the overlay, and release packaging are not implemented.
- Mock/native-compatible data paths are used for service and dashboard validation.
- Battery runtime and process energy values are estimates; process scores are relative indicators,
  not measured watts.
- Automated tests do not validate real hardware sensors.
