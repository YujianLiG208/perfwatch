# Testing Strategy

## Unit Tests

Python unit tests cover deterministic indexed mock collection, analytics helpers and snapshot
enrichment, SQLite insertion and migration, repository queries, event insertion, configuration,
server CLI behavior, and API endpoints.

Phase 3 persistence coverage includes single and batch snapshot writes, transactional rollback,
system and process time-window queries, schema indexes, dashboard metric shaping, top-process
selection, event writes, and retention cleanup.

## Mock Tests

C++ and Python mock tests verify the same index-zero baseline, evolving formulas, repeatability,
cycle boundaries, invalid indices, and independent collector state. Phase 8 keeps mock selection
explicit: native unavailability raises rather than falling back to mock data.

## Fixture Tests

Phase 2 adds fixture-backed C++ tests for Linux parser behavior. The `/proc/stat`, `/proc/meminfo`,
`/proc/<pid>/stat`, and `/sys/class/power_supply/BAT*/uevent` parsers consume fixture strings and
files from `tests/fixtures/linux` instead of reading the host `/proc` or `/sys` filesystem.

The Windows collector uses one focused pure delta/tracker regression check plus one local live smoke;
it does not introduce a hardware matrix or recorded sensor fixtures.

## Service Tests

Phase 4 tests run the FastAPI lifespan and asyncio sampling loop with deterministic collectors. They
verify startup, graceful shutdown, latest snapshot updates, temporary SQLite writes, and collector
error events. HTTP coverage includes `/health`, `/snapshot`, `/metrics/recent`, and
`/processes/top`; WebSocket coverage verifies `/ws/snapshot`.

Every service test uses pytest temporary paths for its database. Tests do not require real hardware
sensors, a Linux VM, or a compiled native module.

Phase 7 service tests verify enrichment occurs before current/persisted assignment, analytics errors
preserve the raw sample, legacy database migration is additive and idempotent, enriched values reach
all HTTP/WebSocket contracts, and static assets coexist with every API route.

## Dashboard Tests

Phase 5 uses Vitest and React Testing Library. Tests cover:

- dashboard loading, current metric rendering, fatal errors, and empty process data;
- snapshot-to-chart mapping, byte/percent formatting, timestamp de-duplication, and the 60-sample
  limit;
- initial Phase 4 HTTP requests and top-process rendering capped at ten rows;
- WebSocket snapshot handling, visible connection modes, bounded reconnect delay selection, and
  five-second HTTP fallback polling;
- the complete 1/2/4/8/10-second reconnect schedule, reset after connection, constructor failure,
  stale fallback response rejection, and unmount cleanup.
- estimated battery-duration formatting and nullable process-score rendering;
- same-origin production HTTP/WebSocket configuration.

HTTP responses and WebSocket connections are deterministic test doubles that mirror the complete
Phase 4 snapshot structure. No frontend test requires a running API or host hardware.

The production frontend build may report a non-blocking Vite advisory because the Recharts bundle
is larger than 500 kB before gzip compression. Exact Phase 7 acceptance counts and command results
are recorded in `docs/Phase 7 integrated local application.md`.

## Phase 7 Full Acceptance

Final acceptance runs the complete Python test suite and Ruff, the complete Dashboard Vitest suite
and production build, the C++ configure/build/CTest flow, a native-backed Python mock test, and an
integrated `TestClient` smoke covering `/`, `/health`, `/snapshot`, `/metrics/recent`,
`/processes/top`, and `/ws/snapshot`.

Native acceptance uses the owner-validated Ninja executable passed explicitly as
`CMAKE_MAKE_PROGRAM`, the validated pybind11 CMake directory, and an MSVC environment loaded in the
same PowerShell process. The exact machine paths belong in the Phase 7 process note, not in this
portable strategy document.

## Phase 8 Minimal Acceptance

Phase 8 deliberately avoids repeating the complete suite for each work item:

- 8A: 45 focused Python contract/service/storage checks, 15 nullable Dashboard checks plus its
  production build, one CTest target, Ruff, and one live native binding smoke.
- 8B: two Overlay model checks, one real Win32 window creation/clean-exit smoke, and focused Ruff.
- 8C: six runtime/server checks, focused Ruff, one Windows package build, required-layout inspection,
  and one explicit-mock package smoke covering `/health`, `/snapshot`, `/`, and exit code zero.
- 8D: one archive command that generated the ZIP/checksum, expanded the ZIP, checked required files,
  and recomputed SHA-256.
- 8E: one static workflow/document consistency group and `git diff --check`; no application suite.

These checks establish contract, composition, and one-machine capability. Phase 9 completed the
separate physical checks for sensor accuracy and stability, battery charge-state behavior, browser
visual review, Overlay layout/topmost/click-through/DPI behavior, and the packaged live full flow
through collection, estimation, persistence, queries, WebSocket streaming, Dashboard/Overlay
display, shutdown, and restart.

## CI Limitations

CI validates deterministic parser/mock contracts and build shape. The Windows release workflow also
builds and smoke-tests the packaged explicit-mock application before creating its ZIP and SHA-256.
Neither workflow validates physical sensor accuracy, live Linux/GPU collection, or browser/Overlay
visual behavior. A release workflow definition is not evidence of a remote run until GitHub reports
one.

## Physical Hardware and Visual Testing

Phase 9 ran the physical hardware and visual checks outside default CI on the project owner's Windows
laptop. Repeat them for future hardware-specific changes; they remain intentionally outside the
deterministic CI gate.
