# Phase 7 Integrated Local Application Design

**Status:** Approved

**Date:** 2026-08-23

**Scope authority:** `README.md` and `docs/roadmap.md`

## Purpose

Phase 7 turns the Phase 1-6 mock-driven baseline into one integrated local application. It connects
the existing battery-runtime and process-energy helpers to every sampled snapshot, makes both
Python and native-compatible mock paths produce deterministic evolving samples, and adds one
production command that serves the FastAPI API, WebSocket, and built React dashboard together.

## Outcomes

- Every successful sample is enriched before it becomes current state or is written to SQLite.
- Battery runtime and process energy values remain explicitly identified as estimates.
- Consecutive mock samples have increasing timestamps and bounded, changing values without using
  randomness or the wall clock.
- Python and C++ mock paths follow the same sample-index contract.
- `perfwatch-server` starts one local Uvicorn process for the API, WebSocket, and built dashboard.
- Existing Vite development behavior remains available for frontend development.
- Phase 7 introduces no new Python or npm dependency.

## Non-Goals

- Live Windows, Linux, or GPU-vendor collection.
- Desktop overlay implementation.
- PyInstaller, wheel asset bundling, installer creation, release archives, checksums, or GitHub
  Release publication.
- Automatically running npm from the Python server.
- A new database framework, migration framework, frontend state framework, or process manager.
- New battery-runtime or process-energy algorithms beyond the existing helpers.

## Platform and Tool Constraints

- Windows is the only Phase 7 runtime target.
- Python remains `>=3.11`; CI continues to validate Python 3.11 and 3.12.
- CI continues to use Node.js 24 for frontend tests and the production build.
- Existing FastAPI, Uvicorn, SQLite, React, Vite, Vitest, CMake, CTest, pybind11, and MSVC tooling
  are reused.
- Ninja 1.13.2 is available in the owner's normal PowerShell but is not discoverable by command
  name in the Codex sandbox. Before any stage that would invoke Ninja, work stops so the owner can
  approve an explicit executable path or resolve the sandbox PATH.
- No work in Phase 7 may introduce a workaround that leaks a sandbox-only path into project code,
  CI, or documentation intended for normal users.

## Architecture

Phase 7 keeps three responsibilities separate:

1. Collectors produce measured or mock input fields. Mock collectors own their sequence position.
2. The analytics enrichment boundary computes estimates from each newly collected snapshot.
3. The application boundary persists and exposes the enriched snapshot, while the production
   server adds static dashboard hosting after API and WebSocket routes.

The sampling data flow is:

```text
collector.collect()
    -> enrich_snapshot()
    -> ServiceState.current_snapshot
    -> SnapshotRepository.add_snapshot()
    -> SQLite
    -> HTTP/WebSocket
    -> dashboard
```

This boundary allows Phase 8 to replace mock collectors with live Windows collectors without
moving estimation logic into platform-specific code.

## Deterministic Evolving Mock Design

### Sample-index contract

Both Python and C++ mock factories accept a non-negative `sample_index`. Index zero reproduces the
current Phase 1 baseline. A stateful `MockCollector` starts at zero, returns that indexed sample,
and increments the index once after every successful `collect()` call.

The timestamp is independent of the service sampling interval so the sequence is reproducible:

```text
timestamp_ms = 1710000000000 + sample_index * 1000
```

The mock values use bounded triangular phases:

```text
position = sample_index % 20
triangle = position if position <= 10 else 20 - position

battery_position = sample_index % 80
battery_triangle = (
    battery_position
    if battery_position <= 40
    else 80 - battery_position
)
```

Python and C++ use these exact formulas:

| Field | Formula |
| --- | --- |
| CPU usage percent | `42.5 + 1.5 * triangle` |
| CPU frequency MHz | `3600.0 + 20.0 * triangle` |
| CPU package power watts | `35.0 + 0.8 * triangle` |
| CPU temperature Celsius | `65.0 + 0.4 * triangle` |
| Memory total bytes | `34359738368` |
| Memory used bytes | `17179869184 + 67108864 * triangle` |
| Battery available | `true` |
| Battery charging | `battery_position > 40` |
| Battery percent | `78.0 - 0.25 * battery_triangle` |
| Battery power watts | `18.5 + 0.3 * triangle` |
| Battery energy remaining Wh | `45.0 - 0.2 * battery_triangle` |
| GPU fields | Existing unavailable baseline, unchanged |
| Process PID and name | Existing `1234` and `mock_process`, unchanged |
| Process CPU percent | `12.5 + 0.7 * triangle` |
| Process RSS bytes | `268435456 + 4194304 * triangle` |
| Process VRAM bytes | `0` |
| Raw process estimated score | `0.42 + 0.01 * triangle` |

The battery phase models a bounded discharge and recharge cycle; the analytics layer suppresses a
runtime estimate while `charging` is true. All percentages, byte counts, temperatures, power
values, and energy values remain within their physical field ranges. No mock value reads the wall
clock, host sensors, random generator, or mutable global state.

The exact formulas are copied into Python and C++ tests so drift is detectable. The sequence must
satisfy these observable requirements:

- index zero exactly matches the existing baseline snapshot;
- indices zero and one differ in timestamp, CPU, memory, battery-power, and process fields;
- repeated calls for the same explicit index return equal snapshots;
- stateful collectors return increasing timestamps;
- samples at and around cycle boundaries remain valid and bounded.

### Python and native-compatible paths

`perfwatch.collectors.mock.get_mock_snapshot(sample_index=0)` remains the pure Python factory.
Python `MockCollector` owns a counter and calls that factory.

C++ `make_mock_snapshot(sample_index)` becomes the matching pure factory, and C++ `MockCollector`
owns its own counter. The pybind `get_mock_snapshot` function accepts the optional index. Python
`NativeCollector` owns a counter and passes it to the native function; when the extension is not
available, it delegates to the Python mock collector.

The convenience `get_snapshot()` function continues to return index zero unless an explicit index
is provided. This preserves a deterministic one-shot CLI response while the service collector is
stateful.

## Snapshot Estimation Design

### Enrichment boundary

A focused analytics function performs snapshot enrichment. It receives the newly collected
dictionary, updates that owned dictionary in place, and returns it. It does not read configuration,
persist data, or own sampling state.

`ServiceState.sample_once()` calls enrichment after collection and before assigning
`current_snapshot` or calling the repository. This single call site covers Python mock, native
mock, and future live collectors.

### Battery runtime

The battery section gains:

```text
estimated_remaining_seconds: float | null
```

The existing `estimate_remaining_seconds()` helper is called only when:

- the battery is available;
- the battery is not charging;
- remaining energy is numeric and non-negative; and
- discharge power is numeric and greater than zero.

Otherwise the field is `null`. The dashboard labels the value as estimated and never presents it
as a measured runtime. Charging and unavailable states display an explicit unavailable message.

### Process energy score

Every process with numeric CPU, RSS, and optional VRAM inputs is passed through the existing
`estimate_process_power_score()` helper. The output remains named `estimated_power_score` and is a
relative score, not watts. Missing or invalid inputs result in `null`, and frontend types and
rendering handle that unavailable state explicitly.

### Error handling

Expected partial-data cases produce `null` estimates without raising. If enrichment raises an
unexpected exception, the service records an `analytics` error event and continues with the raw
snapshot so collection, current-state publication, and persistence do not stop. Collector and
storage failures retain their existing handling.

## Persistence and API Contract

The `samples_system` table gains a nullable
`battery_estimated_remaining_seconds REAL` column. New databases receive it through `schema.sql`.
Existing databases receive it through an idempotent standard-library migration:

1. Read `PRAGMA table_info(samples_system)`.
2. If the column is absent, execute one `ALTER TABLE ... ADD COLUMN` statement.
3. Perform the check during repository initialization before inserts or queries.

No Alembic or schema-version framework is added. The existing process table already has the
nullable `estimated_power_score` column.

System inserts and recent-metric reads include the battery estimate. Current snapshot, recent
metrics, and WebSocket payloads therefore use the same battery shape. Root HTTP paths remain:

- `/health`
- `/snapshot`
- `/metrics/recent`
- `/processes/top`

The WebSocket remains `/ws/snapshot`.

## Dashboard Presentation

The TypeScript battery type gains `estimated_remaining_seconds: number | null`. The process score
type becomes `number | null` so unavailable estimates are honest.

The Battery card shows an explicitly labeled estimated duration when available. Charging,
unavailable, and invalid-input states show text rather than a fabricated duration. Existing
process cards and the process table retain the words `Estimated` and `score`; null scores display
`Unavailable`.

Phase 7 does not add a runtime chart, change the dashboard layout, or add state management. The
existing footer continues to explain that energy-related estimates are not measured watts.

## Integrated Production Entry Point

### Command

The Python project adds:

```text
perfwatch-server = perfwatch.server:main
```

The command accepts:

- `--host`, default `127.0.0.1`;
- `--port`, integer default `8000`; and
- `--dashboard-directory`, defaulting to the source checkout's `ui/dashboard/dist` directory.

The server validates that `index.html` exists before starting Uvicorn. A missing or invalid
dashboard directory produces a concise startup error and does not attempt an npm build. The default
host keeps the application local unless the owner deliberately chooses another bind address.

### FastAPI application

`create_app()` gains an optional dashboard directory. API and WebSocket routers are registered
first. When a valid directory is supplied, FastAPI's existing `StaticFiles` support is mounted at
`/` afterward with HTML mode enabled. Route order ensures static files do not hide API or WebSocket
paths.

The module-level `perfwatch.api.app:app` remains API-only for development and existing tests.
`perfwatch-server` creates the combined application explicitly and passes the application object
to `uvicorn.run()` without reload mode.

### Frontend production URLs

Vite development keeps its current `/api` proxy and `/ws` proxy. A production environment file
sets:

```text
VITE_API_BASE_URL=/
VITE_WS_URL=/ws/snapshot
```

The production bundle therefore calls the FastAPI root endpoints on the same origin, while
development continues to proxy `/api/*` and `/ws/*` to the separately started API.

Phase 7 serves an already built source-tree `dist` directory. Packaging that directory into a
wheel, executable, installer, or release artifact remains Phase 8 work.

## Testing Strategy

Each functional work item follows test-driven development with targeted red-green evidence before
its implementation is considered ready for the separate validation stage.

### Mock evolution

- Python tests cover explicit-index determinism, stateful progression, changing fields, and cycle
  boundaries.
- C++ tests cover the same observable contract for the native factory and collector.
- The pybind target must continue to compile with the indexed function signature.

### Estimation and persistence

- Analytics tests cover discharging, charging, unavailable, invalid, and process-input cases.
- Service tests prove enrichment occurs before current-state assignment and persistence.
- SQLite tests cover new databases, migration of an existing Phase 6 schema, insertion, and recent
  metric reconstruction.
- API and WebSocket tests assert the enriched public shape.
- Frontend tests cover formatted battery estimates and unavailable process scores.

### Production server

- Server tests replace `uvicorn.run` and assert application, host, port, and dashboard arguments.
- API tests use a temporary dashboard directory and prove `/`, HTTP API paths, and WebSocket paths
  coexist.
- Missing dashboard assets fail before Uvicorn starts.
- The existing frontend production build remains the authoritative asset-generation check.

The existing CI workflow structure and dependency manifests remain unchanged except for adding the
new Python console-script declaration and frontend production environment file.

## Functional Work Items and Stage Gates

Phase 7 is split into independently reviewable work items:

1. **Phase 7A:** deterministic evolving Python/C++ mocks and binding contract.
2. **Phase 7B:** estimation enrichment, SQLite migration, API contract, and dashboard labels.
3. **Phase 7C:** production frontend URLs, static hosting, and `perfwatch-server`.
4. **Phase 7D:** documentation and full Phase 7 acceptance evidence.

Each work item uses the repository pipeline in this exact order, stopping after every stage:

```text
Plan only
-> Implement visibly
-> Validate only
-> Update the process note
-> Review the Git diff
-> Commit
```

The written design is reviewed before the detailed implementation plan is created. No
implementation begins until both artifacts are approved. Any stage that reaches a Ninja command
stops before executing it, as required by the owner's explicit instruction.

## Acceptance Criteria

Phase 7 is complete only when:

- consecutive service samples have increasing timestamps and changing deterministic mock values;
- Python and native-compatible collectors satisfy the same indexed mock contract;
- battery runtime and process scores are computed by the existing helpers in the shared sampling
  pipeline;
- estimate fields are explicitly named, persisted, queried, streamed, and displayed as estimates;
- an existing Phase 6 SQLite database upgrades without data loss;
- `perfwatch-server` serves the built dashboard, HTTP API, and WebSocket from one local process;
- Vite development still works with its existing proxy model;
- no Phase 8 live collection, overlay, packaging, or release work is introduced;
- targeted and full validation evidence passes in the appropriate validation stages; and
- README, Roadmap, architecture, data-model, testing, and Phase 7 process documentation match the
  implemented result.
