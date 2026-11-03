# Project Simplification and Architecture Boundaries

This document consolidates the previous *Design and Process Audit* and *Over-implementation Audit*, stripping out temporary branch comparisons, sandbox logs, and step-by-step interaction transcripts. It retains only durable **code reductions, dependency replacements, architectural boundaries, and testing/CI policies** that govern ongoing maintenance.

---

## 1. Core Design Reductions and Architectural Convergence

1. **Removed Uncalled Cross-Platform and Speculative Code**
   - Deleted Linux parsers/collectors, GPU interfaces, platform detection logic, and associated test fixtures that had no production callers and existed only for speculative future plans.
   - Removed the C++ `MockCollector` and the single-implementation `Collector` abstract base class; C++ now retains only the real `WindowsCollector`, while explicit mocks are provided in Python.
2. **Folded Data Access Layer and Redundant APIs**
   - Merged `SnapshotRepository` into `SQLiteWriter`, keeping only initialization, single-snapshot writes, event writes, recent metric queries, and top-process queries actively used by the application.
   - Removed the legacy `perfwatch.cli`, one-shot native `get_snapshot()`, no-op `close()`, and unused batch write, standalone process query, generic time-window, and data retention APIs.
3. **Pruned Dependencies and Historical Process Documentation**
   - Removed `pytest` from runtime dependencies and unused `mypy` from development dependencies.
   - Deleted historical plans/specs under `docs/superpowers`, command-level logs from Phases 3–5, 7, and 8, superseded CI/CD design notes, and the outdated Overlay placeholder document.

---

## 2. Replacing Hand-Rolled Logic with Standard Libraries and Mature Packages

| Module & Location | Previous Hand-Rolled Implementation | Replacement & Preserved Boundaries |
| :--- | :--- | :--- |
| **Windows Overlay**<br>`python/src/perfwatch/overlay/win32.py` | Manual `ctypes` declarations for `WNDCLASSW`, `PAINTSTRUCT`, callback signatures, Win32 constants, and DLL function signatures. | Replaced with Windows-conditional `pywin32==312` (`win32gui`, `win32api`, `win32con`, `win32event`) and `PumpMessages()`. Preserved data model imports and explicit window-creation rejection on non-Windows platforms; suppresses only invalid-window-handle errors after UI thread destruction. |
| **Frontend HTTP Polling**<br>`ui/dashboard/src/useDashboardData.ts` | Manually managed polling timers, request mutexes, `AbortController` lifecycles, stale response generations, and loading states. | Replaced with `@tanstack/react-query@5.102.8` (hook-scoped `QueryClient` using `useQuery`, `refetchInterval`, and `cancelQueries`). Stops polling and cancels in-flight HTTP requests immediately when WebSocket reconnects to prevent stale responses from overwriting live samples. |
| **WebSocket Reconnection**<br>`ui/dashboard/src/useDashboardData.ts`<br>`ui/dashboard/src/connection.ts` | Manually tracked retry counts, backoff timers, socket reconstruction, and unmount cleanup state machine. | Replaced with `partysocket@1.3.0` (`partysocket/ws`) configured with 1/2/4/8/10s backoff, `minUptime: 0`, and a 4s handshake timeout. Triggers HTTP fallback on disconnect or error; clears event callbacks before calling `close()` on unmount. |
| **Process Path & Encoding**<br>`cpp/platform/windows/windows_collector.cpp` | Manual filename extraction via `find_last_of`/`substr` and two-pass `WideCharToMultiByte` UTF-8 conversion. | Replaced with C++17 `std::filesystem::path` (`filename()` and `u8string()`). Returns `"unknown"` on query failure, empty filename, or `std::system_error`. |
| **Boolean Env Parsing**<br>`python/src/perfwatch/config/settings.py` | Hand-written `1/0`, `true/false`, `yes/no`, and `on/off` lookup sets. | Replaced with Python standard library `ConfigParser.BOOLEAN_STATES`, preserving default values, whitespace trimming, case insensitivity, and `ValueError` messages on invalid inputs. |

---

## 3. Explicitly Preserved Architectural Boundaries (Anti-Churn Guardrails)

- **Retain Manual `ProcessorPowerInformation` Declaration**: Microsoft documentation explicitly notes that this structure was omitted from `WinNT.h` and must be defined by the application.
- **No Heavyweight Frameworks**: Keep standard library `sqlite3` (with transactions and `executemany`) without introducing an ORM; retain FastAPI on the backend, and Recharts + native `Intl` on the frontend without extra schedulers or state management libraries.
- **Defer Low-Level Collector Contract Rewrites**: Do not batch-rewrite snapshot field conversions, database mappings, or Python/C++ boundary interfaces, nor migrate the Windows collector to third-party libraries, ensuring field semantics and units remain stable.

---

## 4. Test Suite Pruning and Environment Isolation

1. **Removed and Consolidated Redundant Tests**
   - **Deleted tests for removed code**: Removed all test cases and fixtures covering the deleted Linux parsers and C++ mocks.
   - **Focused SQLite coverage**: Reduced from 14 tests to 4 core risk scenarios (schema migration, real read/write, transaction rollback, and event logging).
   - **Focused frontend hook coverage**: Removed the exhaustive backoff matrix and redundant cleanup branches; retained initial/live data, disconnect fallback, stale response isolation, unmount cleanup, and fatal error scenarios; merged two `Unavailable` state display tests.
   - **Eliminated backend overlap**: Removed the standalone `/health` test (covered by the Dashboard mount integration test), standalone CLI argument parsing test (covered by the service entry test), and duplicate energy score consistency test (covered by the enrichment test); merged service start and stop tests into a single lifecycle test.
2. **Assertions and Execution Isolation**
   - **C++ Release Test Assertions**: Test files explicitly undefine `NDEBUG` before including `<cassert>` so assertions execute in Release builds without altering optimization flags for production binaries.
   - **Lean Packaging and Isolated Smoke Tests**: Reduced release ZIP verification to a single extraction and directory layout check, removing duplicate pre/post hash and checksum self-checks. Packaging smoke tests assign an isolated temporary `LOCALAPPDATA` directory to the child process and clean it up on both normal and abnormal exit to avoid polluting the user's local database.

---

## 5. Path-Based CI Scope Control (`scripts/ci_scope.py`)

Standard-library script `scripts/ci_scope.py` compares changed file paths and selectively triggers check tasks (preserving required status check names `python-cpp`, `frontend`, and `quality` while skipping unrelated work at the job level):

- **Markdown-only changes**: Skip all build and code checks.
- **Frontend directory changes**: Run only frontend tests and the Vite production build.
- **Python source/test changes**: Run backend `pytest` and `Ruff` checks (`Ruff` and test runner environments are decoupled; pure Python edits skip `pybind11` installation and C++ compilation).
- **C++ source or Python dependency config changes**: Trigger backend tests and native C++ extension build checks (a single build verifies both C++ test targets and the Python native extension target).
- **Workflow, script, or packaging config changes**: Run the full check matrix (Windows/Ubuntu × Python 3.11/3.12).