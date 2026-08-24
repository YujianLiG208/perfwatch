# Phase 7 Integrated Local Application

**Status:** Completed — 7A–7C delivered and the non-feature 7D acceptance closeout passed

**Date:** 2026-08-24

**Branch:** `codex/phase7`

**Worktree:** Codex linked worktree `4e73`

## Purpose

Record the implementation and validation evidence for Roadmap Phase 7. This note is updated after
each functional work item. The current record covers Phase 7A deterministic evolving mock samples,
Phase 7B analytics enrichment and persistence, and Phase 7C integrated local production serving.

> **Scope clarification:** Phase 7 has three feature implementation work items: 7A, 7B, and 7C.
> Phase 7D is not a fourth feature; it is the documentation synchronization and full-acceptance
> closeout for those three delivered features.

## Phase 7A — Deterministic Evolving Mock Samples

### Delivered Behavior

- Python and C++ mock factories accept an optional non-negative `sample_index`.
- Index zero preserves the existing Phase 1 baseline snapshot.
- Timestamps advance by 1,000 milliseconds per index from `1710000000000`.
- CPU, memory, battery, and process fields follow the approved bounded triangular formulas.
- GPU fields remain at the existing unavailable baseline.
- Python `MockCollector`, Python `NativeCollector`, and C++ `MockCollector` each own an independent
  counter and increment it after a successful sample.
- Python `get_snapshot()` and the pybind `get_mock_snapshot()` retain index-zero defaults for
  backward-compatible one-shot calls.
- The native-compatible wrapper passes its index to the compiled extension when present and to the
  pure Python factory otherwise.

### Changed Interfaces and Files

| File | Interface or behavior change |
| --- | --- |
| `python/src/perfwatch/collectors/mock.py` | Added `_triangle()`, `get_mock_snapshot(sample_index=0)`, negative-index validation, deterministic formulas, and stateful `MockCollector`. |
| `python/src/perfwatch/collectors/native.py` | Added `get_snapshot(sample_index=0)` and stateful `NativeCollector`; both native and fallback paths receive the index. |
| `python/tests/test_mock_collector.py` | Added baseline, explicit-index, repeatability, independent-state, battery-boundary, invalid-index, native-boundary, and fallback tests. |
| `cpp/include/perfwatch/collector.hpp` | Added the indexed factory declaration and `MockCollector::sample_index_`. |
| `cpp/src/collector.cpp` | Added the integer triangle helper, approved formulas, and successful-collection index advancement. |
| `cpp/bindings/pybind_module.cpp` | Added optional `sample_index` to `get_mock_snapshot` and delegated directly to the indexed factory. |
| `cpp/tests/test_mock_collector.cpp` | Replaced fixed-snapshot equality checks with baseline, indexed, repeatability, cycle-boundary, and independent-state assertions. |

No new dependency, source file, runtime abstraction, hardware collector behavior, endpoint, or
packaging behavior was added.

### Test-Driven Implementation Evidence

| Step | Command or observation | Result |
| --- | --- | --- |
| Python baseline | `python -m pytest python/tests/test_mock_collector.py -q` before new tests | `1 passed` |
| Python mock RED | Same command after indexed tests were added | `8 failed`; the factory rejected the new positional index and collectors returned a fixed timestamp. |
| Python mock GREEN | Same command after the indexed factory and collector were implemented | `8 passed` |
| Native wrapper RED | Same command after native/fallback tests were added | `8 passed, 3 failed`; `get_snapshot()` rejected an index and both native-compatible paths reset state. |
| Native wrapper GREEN | Same command after indexed forwarding and state were implemented | `11 passed` |
| C++ RED | `cmake --build build-phase7` after indexed C++ assertions were added | Compilation failed with MSVC `C2660`: `make_mock_snapshot` did not take one argument. |
| C++ GREEN build | `cmake --build build-phase7` after the factory, collector, and binding were implemented | Core library, test executable, and `perfwatch_native.cp312-win_amd64.pyd` built successfully. |
| C++ targeted GREEN | `ctest --test-dir build-phase7 --output-on-failure -R perfwatch_cpp_tests` | `1/1` passed. |
| Real pybind smoke | Imported the extension directly from `build-phase7` and called indices 0 and 3 | Printed `1710000000000 1710000003000 47.0`; all assertions passed. |

The RED failures matched the missing behavior rather than syntax, test-discovery, or dependency
errors. Production changes were made only after the corresponding failure was observed.

### Stage 3 Validation Evidence

| Validation | Result |
| --- | --- |
| `python -m pytest python/tests/test_mock_collector.py -q` | PASS — `11 passed in 0.04s` |
| `python -m ruff check python/src/perfwatch/collectors python/tests/test_mock_collector.py` | PASS — `All checks passed!` |
| Explicit MSVC/Ninja/Python/pybind11 CMake configure | PASS — `Configuring done` and `Generating done` |
| `cmake --build build-phase7` | PASS — `ninja: no work to do.` |
| `ctest --test-dir build-phase7 --output-on-failure` | PASS — `1/1` passed, 0 failed |

Stage 3 intentionally ran the Phase 7A scoped Python and C++ validation rather than the complete
repository acceptance suite. Full Python, frontend, and native acceptance is performed by the
non-feature Phase 7D closeout.

### Toolchain Paths and Environment Recovery

The validated native toolchain used these exact paths:

| Tool | Validated path |
| --- | --- |
| Ninja | `C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe` |
| MSVC compiler | `C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\HostX64\x64\cl.exe` |
| Python | `C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` |
| pybind11 CMake directory | `C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages\pybind11\share\cmake\pybind11` |
| Visual Studio environment script | `C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\Launch-VsDevShell.ps1` |

Two environment issues were corrected before validation:

1. The shared Python runtime's editable `perfwatch` installation pointed to an older `9bd6`
   worktree. It was reinstalled with `--no-deps -e .\python` from `4e73`, after which the imported
   module path and indexed signature matched the active worktree.
2. MSVC environment variables were not inherited by new PowerShell processes, and the first CMake
   attempt cached `CMAKE_CXX_COMPILER-NOTFOUND`. Native commands now load `Launch-VsDevShell.ps1`
   in the same process. The failed generated directory was preserved during diagnosis as
   `build-phase7-failed-compiler-cache`, and a fresh `build-phase7` configuration identified MSVC
   19.51.36246, Ninja, Python, and pybind11.

The final configure/build/CTest group passed without a Ninja error. The project owner therefore
confirmed that the earlier Ninja path issue is resolved and no additional Ninja-only stop is
required during later Phase 7 work.

### Remaining Limitations

- Mock samples are deterministic fixtures, not live Windows sensor readings.
- GPU data intentionally remains unavailable.
- The process score in a raw Phase 7A mock remains the deterministic fixture value; Phase 7B now
  replaces it at the shared sampling boundary before persistence or API presentation.
- Battery runtime estimation, SQLite migration, and dashboard presentation are delivered by Phase
  7B. The integrated production server is delivered by Phase 7C.
- Packaging, installers, services, and release distribution remain Phase 8 work.

### Commit Scope Adjustment

The first Stage 5 review found that the approved detailed plan and two generated build directories
would prevent the Stage 6 clean-worktree check from succeeding. The project owner authorized a
local return to Stage 4 with these decisions:

- include `docs/superpowers/plans/2026-08-23-phase-7-integrated-local-application.md` in the Phase
  7A documentation commit scope;
- delete `build-phase7` and `build-phase7-failed-compiler-cache` after their validation evidence
  had been recorded because both directories are reproducible generated output; and
- replace a repeated full Stage 5 review with a limited status check proving the detailed plan is
  present and both generated directories are absent.

## Phase 7B — Analytics Enrichment, Persistence, and Dashboard Display

### Delivered Behavior

- `enrich_snapshot()` mutates and returns the collected snapshot at the shared service sampling
  boundary, before the snapshot becomes current or is written to SQLite.
- An available, discharging battery with finite non-negative energy and finite positive power gets
  `estimated_remaining_seconds = energy_remaining_wh / power_watts * 3600`; all other battery
  states and invalid inputs get `None`.
- Every process mapping gets a newly computed `estimated_power_score`. Missing, boolean,
  non-finite, negative, or non-integral inputs produce `None` without removing the process.
- An unexpected enrichment exception is recorded as an `analytics` error. The raw collected
  snapshot still becomes current and is offered to storage; collector-failure behavior is
  unchanged.
- SQLite persists `battery_estimated_remaining_seconds` as a nullable `REAL` and reconstructs it
  as a nullable battery field in recent metrics.
- `/snapshot`, `/metrics/recent`, `/processes/top`, and `/ws/snapshot` expose the enriched values.
- Dashboard types accept nullable estimates, display `Estimated 2h 26m remaining` for the baseline
  sample, and render `Unavailable` instead of calling `.toFixed()` on a null process score.

### Changed Interfaces and Files

| File | Interface or behavior change |
| --- | --- |
| `python/src/perfwatch/analytics/snapshot.py` | Added strict numeric normalization and in-place `enrich_snapshot()`. |
| `python/tests/test_snapshot_enrichment.py` | Added battery, process, invalid-input, replacement, preservation, and identity tests. |
| `python/src/perfwatch/api/service.py` | Added enrichment between collection and current/persisted assignment, with isolated analytics error recording. |
| `python/tests/test_service.py` | Added same-object enrichment/persistence and analytics-fallback tests. |
| `python/src/perfwatch/storage/schema.sql` | Added nullable `battery_estimated_remaining_seconds`. |
| `python/src/perfwatch/storage/sqlite_writer.py` | Added idempotent legacy migration, 20-value insertion, and nullable reconstruction. |
| `python/tests/test_sqlite_writer.py` | Added new-schema, legacy-row preservation, SQL arity, and nullable round-trip tests. |
| `python/tests/test_api.py` | Added enriched HTTP/WebSocket assertions and a deterministic first-sample interval. |
| `ui/dashboard/src/types.ts` | Made battery remaining time and process score explicitly nullable. |
| `ui/dashboard/src/data.ts` | Added `formatDurationSeconds()` with unavailable and rounding boundaries. |
| `ui/dashboard/src/App.tsx` | Added availability-first, then charging battery detail and null-safe process summary rendering. |
| `ui/dashboard/src/components/ProcessTable.tsx` | Added `Unavailable` rendering for null scores. |
| `ui/dashboard/src/test/fixtures.ts` | Updated the API fixture to the enriched baseline values. |
| `ui/dashboard/src/data.test.ts` | Added five duration-format boundaries. |
| `ui/dashboard/src/App.test.tsx` | Added visible remaining-time and null-score behavior tests. |

No third-party dependency or new server, endpoint, analytics formula, packaging behavior, or Phase
8 functionality was added.

### Analytics and Storage Fallbacks

The coordinator rejects booleans even though Python treats them as integers, rejects non-finite
floats, and requires RSS/VRAM byte counts to be non-negative integral values. These checks keep the
existing formula functions unchanged while making the snapshot boundary safe for external or
partial collector data.

`ServiceState.sample_once()` retains three distinct failure boundaries:

1. A collector exception records `source="collector"` and produces no current or persisted sample.
2. An analytics exception records `source="analytics"`, then preserves and persists the raw sample.
3. A storage exception records `source="storage"` after the current snapshot has been retained.

`SQLiteWriter.initialize()` executes the current schema, reads
`PRAGMA table_info(samples_system)`, and conditionally runs:

```sql
ALTER TABLE samples_system ADD COLUMN battery_estimated_remaining_seconds REAL
```

The migration is additive and idempotent. The legacy-schema test creates the exact Phase 6 schema,
inserts a pre-existing row, initializes the current writer, and verifies both the new column and
the preserved timestamp. The system INSERT test verifies 20 columns, 20 placeholders, and 20
values together.

### API and Dashboard Contract

For the baseline sample, the service computes these hand-checked values:

| Field | Enriched value |
| --- | --- |
| `battery.estimated_remaining_seconds` | `8756.756756756757` |
| `top_processes[0].estimated_power_score` | `0.1` |

The API tests assert those values in the current snapshot, recent persisted metrics, latest top
processes, and first WebSocket message. Their sampling interval is 60 seconds so the synchronous
startup sample remains index zero while each request executes; the earlier 10 ms interval allowed
the evolving collector to advance before assertions and did not satisfy the first-sample contract.

`formatDurationSeconds()` rounds to the nearest minute, returns `Unavailable` for null, negative,
or non-finite input, and emits an hour/minute form only when hours are present. Battery detail
prioritizes unavailable hardware, then charging state, then a discharging estimate, then an
unavailable estimate. Both the summary card and process table guard nullable scores before calling
`.toFixed()`.

### Test-Driven Implementation Evidence

| Step | Command or observation | Result |
| --- | --- | --- |
| Enrichment RED | `python -m pytest python/tests/test_snapshot_enrichment.py -q` before the coordinator existed | Collection failed with `ModuleNotFoundError: perfwatch.analytics.snapshot`. |
| Enrichment GREEN | Same command after the minimal coordinator | `13 passed` |
| Service RED | New `sample_once` tests before service integration | `2 failed, 4 deselected`; the estimate was absent and the service had no patchable enrichment symbol. |
| Service GREEN | Same two targeted tests after integration | `2 passed, 4 deselected` |
| SQLite RED | New schema, migration, arity, and round-trip cases | `5 failed, 10 deselected`; the column was absent, INSERT had 19 values, and reconstruction lacked the key. |
| SQLite GREEN | Same targeted cases after schema/writer changes | `5 passed, 10 deselected` |
| API contract first run | Four enriched endpoint/WebSocket cases with the old 10 ms test interval | `4 failed`; requests observed later evolving samples rather than the required first sample. |
| API deterministic GREEN | Same cases after setting the test interval to 60 seconds | `4 passed, 1 deselected` |
| Dashboard RED | Targeted `data.test.ts` and `App.test.tsx` after the owner restored the worktree dependencies | `7 failed, 7 passed`, plus the expected unhandled null `.toFixed()` error. |
| Dashboard GREEN | Same two files after formatter, types, fixture, and null guards | `2` files and `14` tests passed with no unhandled error. |
| Final targeted backend check | Explicit new-test node list across enrichment, service, SQLite, and API | `24 passed` |
| Final targeted dashboard check | `npm test -- --run src/data.test.ts src/App.test.tsx` | `2` files and `14` tests passed. |

### Stage 3 Validation Evidence

| Validation | Result |
| --- | --- |
| `python -m pytest python/tests/test_snapshot_enrichment.py python/tests/test_service.py python/tests/test_sqlite_writer.py python/tests/test_api.py -q` | PASS — `39 passed in 3.29s`; one existing Starlette TestClient/httpx deprecation warning. |
| `python -m ruff check python/src/perfwatch/analytics/snapshot.py python/src/perfwatch/api/service.py python/src/perfwatch/storage python/tests/test_snapshot_enrichment.py python/tests/test_service.py python/tests/test_sqlite_writer.py python/tests/test_api.py` | PASS — `All checks passed!` |
| `npm test -- --run` from `ui/dashboard` | PASS — `4` files and `26` tests passed in `11.91s`. |
| `npm run build` from `ui/dashboard` | PASS — TypeScript checks passed; Vite transformed `583` modules and built in `4.67s`. |

The production build emitted `dist/index.html`, a `5.16 kB` CSS asset, and a `539.37 kB` JavaScript
asset. Vite reported that the JavaScript chunk exceeds its default 500 kB warning threshold. This
is a non-blocking optimization warning; code splitting and build-threshold tuning are not required
by Phase 7B. Generated `dist/` output must remain outside the Phase 7B commit.

### Environment Recovery and Remaining Limitations

The active `4e73` worktree initially had no Dashboard `node_modules`, so Vitest could not load.
The owner ran `npm install` in that worktree and confirmed
`Test-Path .\node_modules\vitest\vitest.mjs` returned `True`. The first sandbox retry then timed
out starting the `App.test.tsx` worker. A normal PowerShell run demonstrated that both files
executed and that the unhandled error was the expected null `.toFixed()` RED, not a worker error.
After explicit resumption, the unchanged command reproduced the functional RED without a worker
timeout and the subsequent GREEN runs completed normally.

Remaining limitations after Phase 7B:

- The Starlette TestClient/httpx deprecation warning remains upstream of this change.
- The production Dashboard bundle remains above Vite's default size warning threshold.
- The local production server and same-origin static mount are delivered by Phase 7C.
- Full repository acceptance and documentation completion belong to the non-feature Phase 7D
  closeout.
- Packaging, installers, services, and release distribution remain Phase 8 work.

## Phase 7C — Integrated Local Production Server

### Delivered Behavior

- The Dashboard production build uses same-origin HTTP and WebSocket roots while the existing Vite
  development proxy remains unchanged.
- `create_app()` accepts an optional Dashboard directory and mounts `StaticFiles` at `/` only after
  the HTTP and WebSocket routers have been registered.
- The module-level `perfwatch.api.app:app` remains API-only because it calls `create_app()` without
  a Dashboard directory.
- The new `perfwatch-server` command defaults to `127.0.0.1:8000`, accepts an explicit Dashboard
  directory, validates its `index.html`, and passes the combined FastAPI application directly to
  `uvicorn.run()` without reload mode.
- A missing Dashboard build exits through `ArgumentParser.error` before Uvicorn is started. The
  server never invokes npm or creates a build automatically.
- No Python or npm dependency was added; the implementation reuses FastAPI/Starlette
  `StaticFiles`, Uvicorn, and Python standard-library argument and path handling.

### Changed Interfaces and Files

| File | Interface or behavior change |
| --- | --- |
| `ui/dashboard/.env.production` | Added same-origin `VITE_API_BASE_URL=/` and `VITE_WS_URL=/ws/snapshot`. |
| `python/src/perfwatch/api/app.py` | Added optional `dashboard_directory` and mounted the Dashboard after all API/WebSocket routes. |
| `python/tests/test_api.py` | Added real temporary `index.html` and asset coverage proving static, HTTP API, and WebSocket coexistence. |
| `python/src/perfwatch/server.py` | Added the import-safe parser, source-tree default path, build validation, and Uvicorn entry point. |
| `python/tests/test_server.py` | Added default/explicit argument, missing-build, and combined-application startup tests. |
| `python/pyproject.toml` | Added `perfwatch-server = "perfwatch.server:main"` without changing the existing `perfwatch` script. |

### CLI, Default Path, and Production URLs

After building the Dashboard, the default local command is:

```powershell
perfwatch-server
```

The equivalent explicit form and a custom build-directory example are:

```powershell
perfwatch-server --host 127.0.0.1 --port 8000
perfwatch-server --dashboard-directory C:\path\to\dashboard\dist
```

`default_dashboard_directory()` resolves from `python/src/perfwatch/server.py` to the source
checkout's `ui/dashboard/dist` directory. This is intentionally a source-tree default; bundling
Dashboard assets into a wheel, executable, installer, or release remains Phase 8 work.

The production environment contains exactly:

```dotenv
VITE_API_BASE_URL=/
VITE_WS_URL=/ws/snapshot
```

The existing frontend strips the trailing API slash, so HTTP requests resolve to `/health`,
`/snapshot`, `/metrics/recent`, and `/processes/top`. WebSocket requests resolve directly to
`/ws/snapshot`. Vite development continues to proxy `/api` and `/ws` and does not use a modified
development configuration.

### Mount Order and Failure Boundary

The application factory creates its service and lifespan first, then registers the HTTP router,
then the WebSocket router, and finally mounts `StaticFiles(directory=dashboard_directory,
html=True)` at `/`. Starlette evaluates routes in registration order, so the final catch-all mount
serves `/` and `/assets/*` without shadowing `/health`, `/snapshot`, the metrics/process endpoints,
or `/ws/snapshot`.

The CLI resolves the selected Dashboard directory and checks for `index.html` before composing the
application. Invalid input produces argparse exit code 2 and does not call Uvicorn. For valid
input, one combined FastAPI application object is passed to `uvicorn.run()` with the selected host
and integer port.

### Test-Driven Implementation Evidence

| Step | Command or observation | Result |
| --- | --- | --- |
| Static/API/WebSocket RED | New coexistence test before changing `create_app()` | `1 failed`; `create_app()` rejected the new `dashboard_directory` argument. |
| Static/API/WebSocket GREEN | Same targeted test after the optional mount was implemented | `1 passed`; `/`, `/assets/app.js`, `/health`, `/snapshot`, and `/ws/snapshot` coexisted. |
| Server RED | `python -m pytest python/tests/test_server.py -q` before `perfwatch.server` existed | Collection stopped with the expected missing-module import error. |
| Server first GREEN attempt | Same command after the minimal server implementation | `3 passed, 1 failed`; the failure was a test-only assumption that every FastAPI route wrapper exposes `.name`. |
| Server GREEN | Same command after using a safe route-name lookup in the assertion | `4 passed`. |
| Final Stage 2 target | `python -m pytest python/tests/test_server.py python/tests/test_api.py -q` | `10 passed`; one existing Starlette TestClient/httpx deprecation warning. |

### Stage 3 Validation Evidence

| Validation | Result |
| --- | --- |
| `npm run build` from `ui/dashboard` | PASS — TypeScript checks passed; Vite transformed `583` modules and built in `1.22s`. |
| `Test-Path -LiteralPath dist/index.html` from `ui/dashboard` | PASS — `True`. |
| `python -m pytest python/tests/test_server.py python/tests/test_api.py -q` | PASS — `10 passed in 2.39s`; one existing Starlette TestClient/httpx deprecation warning. |
| `python -m ruff check python/src/perfwatch/api/app.py python/src/perfwatch/server.py python/tests/test_api.py python/tests/test_server.py` | PASS — `All checks passed!` |
| Non-blocking `TestClient` smoke | PASS — `/`, `/health`, and `/snapshot` returned 200; `/ws/snapshot` returned first-sample timestamp `1710000000000`. |

The build emitted `dist/index.html`, a `5.16 kB` CSS asset, and a `539.37 kB` JavaScript asset. Vite
again reported its non-blocking warning for a chunk above 500 kB. Generated `dist/` output remains
outside the Phase 7C commit. The smoke used a temporary SQLite database and closed its TestClient;
it did not start or leave behind a standalone Uvicorn process.

### Remaining Limitations After Phase 7C

- The Starlette TestClient/httpx deprecation warning remains upstream of this change.
- The production Dashboard bundle remains above Vite's default size warning threshold.
- The default server path supports a built source checkout; packaged asset discovery remains Phase
  8 work.
- Full repository acceptance and final documentation belong to the non-feature Phase 7D closeout.
- Live collection, overlays, packaging, installers, services, and distribution remain outside the
  completed 7A–7C scope.

## Phase 7D — Documentation and Full Acceptance Closeout (Not a Feature)

Phase 7D adds no product behavior. It synchronizes the documentation for the three Phase 7 feature
deliveries (7A–7C), runs the complete repository acceptance set, and records the evidence required
to close Phase 7 without claiming Phase 8 work.

### Dependency State

No dependency was installed or upgraded during acceptance.

| Command | Result |
| --- | --- |
| `python --version` | Exit 0 — `Python 3.12.13` |
| `node --version` | Exit 0 — `v26.3.0` |
| `npm --version` | Exit 0 — `11.16.0` |
| `cmake --version` | Exit 0 — `4.2.3` |
| `git --version` | Exit 0 — `2.53.0.windows.1` |

### Full Acceptance Evidence

| Validation | Result |
| --- | --- |
| `python -m pytest python/tests -q` | Exit 0 — `59 passed in 3.94s`; one existing Starlette TestClient/httpx deprecation warning. |
| `python -m ruff check python/src python/tests` | Exit 0 — `All checks passed!` |
| `npm test -- --run` from `ui/dashboard` | Exit 0 — `4` files and `26` tests passed in `11.31s`. |
| `npm run build` from `ui/dashboard` | Exit 0 — TypeScript checks passed; Vite transformed `583` modules and built in `600ms`. |
| Explicit MSVC/Ninja/Python/pybind11 CMake configure | Exit 0 — MSVC `19.51.36246.0`; configuration and generation completed. |
| `cmake --build build-phase7` | Exit 0 — all `20` Ninja build steps completed, including `perfwatch_native.cp312-win_amd64.pyd`. |
| `ctest --test-dir build-phase7 --output-on-failure` | Exit 0 — `1/1` passed, 0 failed in `0.14s`. |
| Native-backed `python -m pytest python/tests/test_mock_collector.py -q` | Exit 0 — the extension loaded from the active `4e73/build-phase7` directory and `11 passed in 0.05s`. |
| Integrated `TestClient` smoke | Exit 0 — `/`, `/health`, `/snapshot`, `/metrics/recent`, and `/processes/top` returned 200; `/ws/snapshot` returned timestamp `1710000000000`; the enriched battery estimate was present. |

The first integrated smoke attempt exited 1 before application startup because the one-off verifier
imported `Settings` from `perfwatch.config`, whose `__init__.py` does not re-export that class. The
repository consistently imports it from `perfwatch.config.settings`. The owner authorized a rerun
with only that verifier import corrected; the unchanged endpoint and data assertions then passed.
No product file was changed for this verifier-only correction.

### Native Acceptance Paths

The native acceptance loaded the Visual Studio development environment in the same PowerShell
process and used these explicit paths:

| Input | Path |
| --- | --- |
| Ninja (`CMAKE_MAKE_PROGRAM`) | `C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe` |
| MSVC compiler selected after environment load | `C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\HostX64\x64\cl.exe` |
| Python (`Python3_EXECUTABLE`) | `C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` |
| `pybind11_DIR` | `C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages\pybind11\share\cmake\pybind11` |
| Visual Studio environment script | `C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\Launch-VsDevShell.ps1` |

The configure, build, and CTest group completed without a Ninja path error, confirming the earlier
path issue remains resolved. `PYTHONPATH` was changed only inside the native-backed test process to
select the generated extension and current worktree sources; no user or system environment was
permanently changed.

### Generated Output and Remaining Limitations

- `ui/dashboard/dist` and `build-phase7` were regenerated only for acceptance. Neither belongs in
  the documentation commit; the reproducible native build directory is removed after its evidence
  is recorded, and the ignored Dashboard build remains unstaged.
- The Dashboard JavaScript asset remains `539.37 kB` and triggers Vite's non-blocking 500 kB chunk
  advisory.
- The existing Starlette TestClient/httpx deprecation warning remains upstream of this change.
- The default production asset path supports a built source checkout. Live Windows collection,
  overlays, packaging, installers, services, release artifacts, and distribution remain Phase 8.
- Physical sensor and browser/overlay visual validation remains Phase 9 work.

## Completion Boundary

Phase 7 is complete with three delivered feature work items (7A–7C) and one non-feature documentation
and acceptance closeout (7D). The worktree passed the final documentation diff and generated-output
review before the six approved documentation files were committed. Phase 8 remains the next planned
implementation phase; no Phase 8 behavior is claimed here.
