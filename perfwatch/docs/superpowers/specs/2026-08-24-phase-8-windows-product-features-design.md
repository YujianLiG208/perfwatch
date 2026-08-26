# Phase 8 Windows Product Features Design

**Status:** Approved design

**Date:** 2026-08-24

## Purpose

Phase 8 turns the completed mock-driven Phase 7 baseline into a packaged Windows product. It adds
live Windows collection, a native Win32 overlay implemented through Python `ctypes`, a directory-mode
Windows runtime, a versioned ZIP and SHA-256 checksum, and GitHub Release automation with final
documentation closeout.

The phase remains Windows x64 only. Live Linux collection and GPU vendor adapters remain deferred
long-term work and are not Phase 8 acceptance requirements.

## Approved Work Items and Process

Phase 8 is divided into five independently reviewable work items:

| Work item | Deliverable | Process |
| --- | --- | --- |
| 8A | Live Windows CPU, memory, battery, and process collection | Repository six-stage pipeline |
| 8B | Python `ctypes` native Win32 overlay | Repository default three-stage pipeline |
| 8C | PyInstaller Windows directory-mode runtime | Repository six-stage pipeline |
| 8D | Versioned Windows x64 ZIP and SHA-256 checksum | Repository six-stage pipeline |
| 8E | GitHub Release automation and documentation closeout | One scoped implementation and validation pass; exempt from the six-stage pipeline |

Work items 8A, 8C, and 8D use the repository's risk-based six-stage pipeline. Work item 8B is an
isolated reversible UI change and uses the default three-stage pipeline. Work item 8E retains the
owner-approved one-pass exception, with focused validation and scoped diff review before commit.

## Global Constraints

- Windows x64 is the only Phase 8 runtime, packaging, and release target.
- Mock data is used only when `PERFWATCH_USE_MOCK_COLLECTOR=true` or an equivalent explicit package
  smoke option is selected.
- A live collector failure never switches to mock data and never merges mock fields into a real
  snapshot.
- Unavailable measurements are represented as `null` and displayed as `N/A`; numeric zero is not
  used to impersonate an unavailable measurement.
- CPU package power and temperature remain nullable because Windows does not expose a reliable
  vendor-neutral measurement on all supported hardware.
- GPU vendor collection and process VRAM collection remain unavailable and do not add vendor SDKs.
- The overlay uses Python `ctypes` with Win32 User32/GDI APIs. Tkinter, Tcl/Tk, Qt, Electron,
  WebView2, and another GUI framework are prohibited.
- PyInstaller 6.22.2 directory mode is the approved runtime assembly mechanism.
- The release artifact is an unsigned Windows x64 ZIP with a SHA-256 file. MSI, MSIX, installers,
  automatic updates, and code signing are out of scope.
- Tests are minimal and risk-focused. Do not generate per-function test suites, broad mock matrices,
  duplicate acceptance checks, or rerun unrelated full suites at every work item.
- Physical hardware accuracy, visual appearance, click-through behavior, DPI behavior, and the
  complete packaged workflow remain Phase 9 validation responsibilities.

## Architecture

The Phase 8 production data flow is:

```text
Windows APIs and PDH
        |
        v
C++ WindowsCollector
        |
        v  pybind11
Python enrichment -> SQLite -> FastAPI HTTP/WebSocket
                                  |              |
                                  v              v
                              Dashboard    ctypes Win32 Overlay
```

The existing enrichment, repository, HTTP, WebSocket, and Dashboard boundaries remain authoritative.
The overlay consumes the existing `GET /snapshot` response and does not introduce a dedicated API,
IPC protocol, database reader, or second snapshot model.

## 8A: Live Windows Collection

### Native collector

Add a stateful `WindowsCollector` behind the existing C++ `Collector` interface. The implementation
uses Windows SDK APIs already present in the validated environment:

- CPU usage uses an English PDH total-processor counter so localized Windows counter names do not
  change the query. The first sample is nullable because a rate counter has no previous sample.
- CPU frequency uses the Windows power-information API and aggregates available logical-processor
  readings. Package power and temperature remain nullable when the OS provides no trustworthy
  vendor-neutral values.
- Memory uses `GlobalMemoryStatusEx`; used bytes equal total physical bytes minus available physical
  bytes.
- Battery presence and status use `GetSystemPowerStatus` and `CallNtPowerInformation`. Percentage,
  rate, energy, and charging state are populated only when Windows returns valid values.
- Processes are enumerated with Windows process APIs. CPU percentages use differences between
  cumulative `GetProcessTimes` values across collector samples, normalized by elapsed time and
  logical processor count. RSS uses `GetProcessMemoryInfo`.
- Process state is keyed by PID plus creation time so PID reuse cannot inherit a previous process's
  CPU baseline. Processes that exit or deny access during a sample are skipped.
- Top processes are selected from valid readings without fabricating unavailable fields. Process
  VRAM remains nullable.

Windows headers and libraries are compiled and linked only under `WIN32`; Linux fixture/parser and
compile-safe boundaries remain unchanged.

### Nullable contract and errors

Native snapshot members that can be unavailable become `std::optional`. pybind11 maps empty values
to Python `None`, which remains `null` through SQLite and API serialization. Dashboard and overlay
formatters render those values as `N/A`.

Partial collection failures preserve the rest of the real snapshot. The native binding may attach a
reserved internal `_collection_issues` list. The Python service removes that key before persistence
or publication and records only the first occurrence of a stable issue code, preventing an event
row from being written every sampling interval. Expected unsupported metrics are reported once as
capability information rather than repeated errors.

A collector-wide failure raises an exception. The service records it and retains the last real
snapshot; it does not construct a replacement snapshot and does not activate the mock collector.
The packaged Windows runtime requires the native extension unless mock mode was explicitly selected.

### Minimal 8A validation

- One focused C++ test file covers first-sample behavior, CPU/process delta arithmetic, invalid
  intervals, and PID reuse.
- One existing Python native-boundary test is extended to prove that a native failure is propagated
  and never replaced by mock data.
- Existing contract tests are adjusted only where nullable fields change approved behavior.
- Live sensor accuracy and hardware-specific availability are not simulated; they are Phase 9 work.

## 8B: Native Win32 Overlay

### Window and rendering

The overlay is Python code that calls User32/GDI directly through `ctypes`. It creates one topmost,
non-activating, tool-window-style layered window. `HTTRANSPARENT` provides mouse click-through. The
window uses the system DPI, a fixed compact layout at the top-right of the primary work area, a
semi-transparent dark background, and GDI text.

The display is intentionally limited to current CPU, memory, battery/remaining-time, available
power, the highest-load process, and connection freshness. It adds no chart, animation, tray icon,
settings window, theme framework, drag persistence, or global hotkey. Nullable values display as
`N/A`.

### Data and lifetime

A background thread uses the already-installed `httpx` dependency to request `GET /snapshot` once
per second. It converts the response into a small display model protected by a lock, then calls
`PostMessageW` so the Win32 UI thread can repaint. Network work never runs inside the window
procedure.

Before the service is reachable, the overlay displays `Waiting for service`. After a connection
failure, it keeps the last real values visible but marks them `STALE`; it never substitutes mock
values. Source-tree execution exits with console `Ctrl+C`. The 8C product launcher owns the packaged
overlay child process and shuts it down with the application.

### Minimal 8B validation

- One Python test file covers snapshot formatting, nullable `N/A` output, waiting state, and stale
  state.
- Automated validation performs one Windows window creation and clean-exit smoke check.
- Individual `ctypes` structures and Win32 constants do not receive repetitive tests.
- Visual appearance, click-through, and DPI behavior are explicitly deferred to Phase 9.

## 8C: Windows Directory-Mode Runtime

### Product launcher

PyInstaller 6.22.2 builds one directory-mode product with one public `perfwatch.exe` entry point.
The launcher:

1. Creates `%LOCALAPPDATA%\PerfWatch` and uses it for the default SQLite database.
2. Starts the existing FastAPI/Uvicorn application on a background thread.
3. Waits for the local service to become ready.
4. Starts the same frozen executable with the private `--overlay-child` argument.
5. Prints the local Dashboard address in the console.
6. On `Ctrl+C`, requests Uvicorn shutdown, terminates the overlay, and waits for clean exit.

The public launcher supports an explicit `--mock` switch for package smoke checks and a
`--no-overlay` switch for non-GUI automation. Production defaults to the native Windows collector.
It does not install a service, add startup registration, open a tray application, or create an
installer.

### Bundle contents

The PyInstaller spec explicitly includes the Python runtime and dependencies, the Release-built
`perfwatch_native` extension, Dashboard production assets, SQLite schema, README, and LICENSE. The
native import is declared explicitly because the current collector wrapper imports it dynamically.

```text
perfwatch/
|-- perfwatch.exe
|-- _internal/
|   |-- perfwatch_native.pyd
|   |-- dashboard/
|   `-- perfwatch/storage/schema.sql
|-- README.md
`-- LICENSE
```

The source-tree `perfwatch-server` entry point remains available for development. Packaged resource
resolution uses the frozen bundle root while source execution retains existing source-relative
paths.

### Build and minimal 8C validation

The build order is Dashboard production build, CMake Release native build, and PyInstaller assembly.
The single package smoke starts `perfwatch.exe --mock --no-overlay`, checks `/health`, `/snapshot`,
and the Dashboard root, then shuts down and verifies no product process remains. It does not repeat
the full 8A or 8B suites.

## 8D: ZIP and SHA-256

8D consumes the already validated 8C directory and does not rebuild it. A PowerShell script reads
the sole project version from `python/pyproject.toml` with Python standard-library `tomllib`, checks
the required bundle contents, and produces:

```text
release/perfwatch-<version>-windows-x64.zip
release/perfwatch-<version>-windows-x64.zip.sha256
```

`Compress-Archive` creates the ZIP. `Get-FileHash -Algorithm SHA256` writes the checksum as
`<hash>  <filename>`. Validation expands the archive into a temporary directory once, checks the
required files, and recomputes the checksum. Release binaries remain untracked and are not committed.
No application test suite is rerun in 8D.

## 8E: GitHub Release and Documentation Closeout

8E is intentionally not expanded into another separately approved design. It performs one scoped
implementation and validation pass that:

- adds a Windows-only release workflow for pushed tags matching exact `vMAJOR.MINOR.PATCH` syntax;
- retains `workflow_dispatch` for build verification without publication;
- requires the tag version to match `python/pyproject.toml`;
- builds the approved 8C directory and 8D ZIP/checksum on a Windows x64 runner;
- publishes only after build and package smoke checks succeed;
- grants `contents: write` only to the publish job and uses the repository-scoped `GITHUB_TOKEN`;
- uploads the ZIP and SHA-256 file to one GitHub Release with generated release notes;
- records that the artifact is unsigned; and
- updates README, Roadmap, architecture, data model, testing strategy, CI/CD documentation, and the
  Phase 8 process note to match verified behavior.

The work item receives one workflow/static consistency check and one scoped Git diff review. It does
not rerun unrelated application test suites merely because documentation changed.

## Expected File Areas

The implementation plan may refine exact paths, but work remains within these areas:

- `cpp/include/perfwatch/`, `cpp/platform/windows/`, `cpp/bindings/`, `cpp/tests/`, and
  `cpp/CMakeLists.txt` for 8A;
- `python/src/perfwatch/collectors/`, `python/src/perfwatch/api/service.py`, nullable contract
  consumers, and focused Python tests for 8A;
- `python/src/perfwatch/overlay/` and one focused overlay test for 8B;
- `python/src/perfwatch/` runtime entry points, `python/pyproject.toml`, a PyInstaller spec, and a
  focused Windows build script for 8C;
- a focused PowerShell archive script and `.gitignore` release-output entry for 8D; and
- `.github/workflows/`, project documentation, and the Phase 8 process note for 8E.

Unrelated refactors, dependency upgrades, frontend redesign, new API endpoints, installer projects,
and future platform work are excluded.

## Acceptance Criteria

Phase 8 is complete when all of the following are supported by scoped validation evidence:

- The default Windows runtime produces live CPU, memory, battery, and process data without mock
  contamination.
- Unavailable measurements remain nullable and visible as unavailable.
- Partial collector failures preserve other real readings and do not flood the events table.
- Explicit mock mode remains deterministic and available for tests and package smoke checks.
- The Win32 overlay consumes the existing local snapshot API, remains click-through and topmost, and
  clearly marks waiting, stale, and unavailable states.
- The directory-mode product contains the native extension, Dashboard, schema, dependencies,
  README, and LICENSE and shuts down without leaving an overlay process.
- The versioned Windows x64 ZIP expands successfully and its SHA-256 file verifies.
- Manual workflow dispatch can validate the release build without publishing.
- A valid matching version tag can publish the unsigned ZIP and checksum with minimal permissions.
- Documentation distinguishes Phase 8 automated evidence from Phase 9 physical hardware and visual
  acceptance.

## Explicit Phase 9 Boundary

Phase 8 automated checks prove code paths, bundle shape, and release mechanics. Phase 9 remains
responsible for the project owner's physical Windows laptop validation, sensor availability and
stability, Dashboard browser review, overlay appearance and click-through behavior, and the complete
packaged collect-estimate-persist-query-stream-display-overlay-shutdown-restart workflow.
