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
cycle boundaries, invalid indices, and independent collector state. The native-compatible Python
wrapper is tested both with a compiled extension and with its pure-Python fallback.

## Fixture Tests

Phase 2 adds fixture-backed C++ tests for Linux parser behavior. The `/proc/stat`, `/proc/meminfo`,
`/proc/<pid>/stat`, and `/sys/class/power_supply/BAT*/uevent` parsers consume fixture strings and
files from `tests/fixtures/linux` instead of reading the host `/proc` or `/sys` filesystem.

Windows fixtures remain placeholders for later collector work.

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

## CI Limitations

CI can validate deterministic parser and mock code paths plus build shape. Deterministic mocks and
fixtures do not validate physical sensors or live Linux, Windows, or GPU collection. The service
suite validates backend orchestration through the mock/native-compatible collector interface, and
the Dashboard suite validates browser behavior through mocked network boundaries. Browser visual
QA remains an additional local check rather than a hardware test.

## Future Real-Hardware Testing

Later phases should add opt-in local hardware tests that are excluded from default CI.
