# Testing Strategy

## Unit Tests

Python unit tests cover deterministic mock collection, simple analytics helpers, SQLite insertion,
repository queries, event insertion, configuration, and API endpoints.

Phase 3 persistence coverage includes single and batch snapshot writes, transactional rollback,
system and process time-window queries, schema indexes, dashboard metric shaping, top-process
selection, event writes, and retention cleanup.

## Mock Tests

C++ and Python mock tests verify stable values and expected keys. This is the Phase 1 test anchor.

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

HTTP responses and WebSocket connections are deterministic test doubles that mirror the complete
Phase 4 snapshot structure. No frontend test requires a running API or host hardware.

Before Phase 3 integration, the Phase 5 baseline validation completed with 20 frontend tests,
16 Python tests, and one C++ test passing. That Python suite retained a Starlette/httpx deprecation
warning. The production frontend build succeeded and reported a non-blocking Vite advisory because
the single Recharts bundle was larger than 500 kB before gzip compression. Fresh Task 3 integration
results are recorded in the integration plan after validation rather than predicted here.

## CI Limitations

CI can validate deterministic parser and mock code paths plus build shape. Deterministic mocks and
fixtures do not validate physical sensors or live Linux, Windows, or GPU collection. Phase 4
validates backend orchestration through the mock/native-compatible collector interface, and Phase 5
validates browser behavior through mocked network boundaries. Browser visual QA remains an
additional local check rather than a hardware test.

## Future Real-Hardware Testing

Later phases should add opt-in local hardware tests that are excluded from default CI.
