# Phase 8 Windows Product Features

## 8A — Live Windows Collection

### Risk and scope

8A used the six-stage pipeline because it changed the shared nullable snapshot contract across C++,
pybind11, Python, SQLite/API consumers, and TypeScript. No database migration was required: existing
SQLite metric columns already accept `NULL`, and rollback is the eventual 8A commit revert.

The implementation was reduced from the original plan after inspecting the real flow. It reuses the
existing `Collector`, `ServiceState`, enrichment, repository, API, and Dashboard boundaries. One
`WindowsCollector` owns the necessary Windows handles and process baselines; PDH and process tracking
remain private implementation details rather than separate public classes. The unused PDH and WMI
placeholder sources were removed.

### Implemented behavior

- Windows total CPU uses the English PDH counter; its first rate sample remains `null`.
- CPU frequency uses `CallNtPowerInformation`; package power and temperature remain `null` when no
  trustworthy generic Windows source exists.
- Memory uses `GlobalMemoryStatusEx`.
- Battery presence, charging, percentage, rate, and remaining energy use Windows power APIs and are
  populated only when the returned values are valid.
- Processes use Windows process APIs, PID plus creation time for CPU baselines, working-set RSS, and
  a maximum of ten rows. Unavailable VRAM and derived score remain `null` rather than using zero.
- The native binding exposes `_collection_issues` only as an internal transport key. `ServiceState`
  removes it before publication or persistence and records each stable issue code once.
- `NativeCollector` raises when the native extension is unavailable. Mock data is selected only by
  the existing explicit mock setting.
- Dashboard types, charts, cards, and process formatting preserve nullable measurements and display
  `Unavailable` rather than a fabricated zero.

### Validation evidence

| Gate | Result |
| --- | --- |
| Focused Python contract, service, enrichment, and SQLite tests | `45 passed` |
| Focused Python Ruff check | PASS |
| Dashboard nullable tests | `15 passed` |
| Dashboard TypeScript and Vite production build | PASS; existing bundle-size warning retained |
| Native Release configure and build | PASS with MSVC 19.51 and Ninja |
| CTest | `1/1` passed |
| Live native binding smoke | PASS; non-mock timestamp, real memory/frequency/battery data, ten processes |

Validated paths remained:

- Visual Studio environment: `C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\Launch-VsDevShell.ps1`
- Ninja: `C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe`
- Python: `C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
- pybind11 CMake directory: `C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages\pybind11\share\cmake\pybind11`

The live smoke observed the expected first-sample limitations: PDH CPU usage was `null`, and generic
CPU package power and temperature were unavailable. Frequency, memory, battery, and process data were
present. This is capability evidence only, not a sensor-accuracy claim.

### Remaining Phase 9 boundary

Physical-hardware accuracy, long-running sensor stability, battery behavior across charge states,
process ranking accuracy, Dashboard browser review, and complete packaged-flow acceptance remain
Phase 9 responsibilities. No GPU vendor adapter, installer, service, signing, or Linux live collector
was added.

## 8B — Native Win32 Overlay

### Scope and implementation

8B used the default three-stage pipeline because it consumes the existing local `/snapshot` API and
does not change collection, persistence, shared contracts, security, packaging, or release behavior.
The implementation adds no dependency: Python calls User32 and GDI32 directly through `ctypes`, while
the already-installed `httpx` client performs network requests on one daemon thread.

`OverlayModel`, `model_from_snapshot`, and `stale_model` define the small display boundary. The model
shows CPU usage and frequency, memory, battery and remaining time, CPU and battery power, the highest-
load process, and connection freshness. Missing, invalid, or non-finite measurements render as `N/A`.
Before the first response it shows `Waiting for service`; after a connection failure it preserves the
last real model and marks it `STALE`. It never obtains or substitutes mock values.

`Win32OverlayWindow` owns one fixed top-right layered tool window, its callback, and its GDI font. The
window is topmost, non-activating, and returns `HTTRANSPARENT` for hit testing. The UI thread performs
only message handling and GDI painting; the HTTP worker publishes models through `PostMessageW`.
`perfwatch-overlay` and `python -m perfwatch.overlay` accept the snapshot URL, sampling interval, and
optional parent PID needed by the 8C launcher. No Tk, Qt, tray icon, settings UI, animation, theme
framework, drag persistence, or global hotkey was added.

### Validation evidence

| Gate | Result |
| --- | --- |
| `python -m pytest python/tests/test_overlay.py -q` | `2 passed` |
| Windows window creation and clean-exit smoke | PASS |
| `python -m ruff check python/src/perfwatch/overlay python/tests/test_overlay.py` | PASS |

The smoke proves that the real Win32 class and window can be created and shut down cleanly on the
current Windows environment. It does not claim visual correctness.

### Remaining Phase 9 boundary

Overlay appearance, text layout on physical displays, topmost and click-through interaction, DPI and
scaling behavior, long-running freshness behavior, and complete packaged overlay lifecycle validation
remain Phase 9 responsibilities.

## 8C — Windows Directory-Mode Runtime

### Scope and implementation

8C used the six-stage pipeline because it adds the product entry point, coordinates Uvicorn and the
Overlay child process, resolves frozen resources and mutable data, and defines the distributable
directory layout. `perfwatch.runtime` reuses the existing `create_app()`, `Settings`, Dashboard, native
collector, and Overlay boundaries; it adds no launcher or service abstraction.

The public `perfwatch` entry point accepts host, port, database, Dashboard, explicit mock, and
no-Overlay options. The packaged default stores mutable data under `%LOCALAPPDATA%\PerfWatch`, while
Dashboard, SQLite schema, and the native extension remain in the frozen bundle. One non-daemon thread
runs Uvicorn, the main console thread owns startup and shutdown, and an optional child process runs the
same executable in private Overlay mode. Windows `SIGBREAK` is converted to the existing
`KeyboardInterrupt` cleanup path so the targeted Ctrl+Break smoke exits with code zero.

PyInstaller 6.22.2 creates one console directory product with `_internal` contents. The build script
requires validated Ninja, Visual Studio shell, pybind11 CMake directory, and Python paths; it removes
only the explicit repository-owned product and PyInstaller work directories before rebuilding.

### Build evidence

The validated command was:

```powershell
& .\scripts\build_windows_package.ps1 `
  -NinjaPath 'C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe' `
  -VsDevShellPath 'C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\Launch-VsDevShell.ps1' `
  -Pybind11Directory 'C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages\pybind11\share\cmake\pybind11' `
  -PythonPath 'C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
```

| Gate | Result |
| --- | --- |
| Focused runtime/server tests | `6 passed` |
| Focused Ruff check | PASS |
| Dashboard TypeScript and Vite build | PASS; existing bundle-size and plugin-timing advisories retained |
| Native Release configure/build | PASS; Ninja reported no work required |
| PyInstaller | `6.22.2`, PASS in approximately 171.7 seconds |
| Complete build wall time | Approximately 3 minutes 20 seconds |
| Packaged `/health`, `/snapshot`, and `/` smoke | HTTP 200 for all three endpoints |
| Explicit mock assertion | PASS; deterministic baseline timestamp observed |
| Ctrl+Break shutdown | PASS; Uvicorn shutdown completed and process exit code was zero |
| Required directory layout | PASS |

The final `dist/perfwatch` directory contained 814 files totaling 88,274,952 bytes (84.19 MiB).
The product root contained `perfwatch.exe`, `README.md`, and `LICENSE`; `_internal` contained
`perfwatch_native.cp312-win_amd64.pyd`, `dashboard/index.html`, and
`perfwatch/storage/schema.sql`.

The final smoke ran outside the Codex filesystem sandbox because the packaged product intentionally
writes its database to real LocalAppData. A direct SQLite probe and Windows ACL inspection confirmed
that the target directory itself was writable; this was a test-harness boundary, not a product
fallback or a change to the packaged data location.

### Distribution and Phase 9 boundary

8C produces an unsigned directory-mode application only. It adds no installer, signing, service,
startup registration, ZIP, checksum, or release publication; ZIP and SHA-256 remain 8D work. The
automated mock smoke proves bundle composition, HTTP behavior, and clean shutdown, but physical live
sensor stability, Overlay appearance and interaction, and the complete packaged live workflow remain
Phase 9 responsibilities.

## 8D — ZIP and SHA-256

### Scope and implementation

8D used the six-stage pipeline because it creates the release-gating Windows artifact. It consumes
the already validated 8C `dist/perfwatch` directory without rebuilding it. The release script reads
version `0.1.0` from `python/pyproject.toml`, requires the approved product layout, and uses only
PowerShell archive, hash, and temporary-directory facilities.

Before replacing output, the script limits removal to the exact versioned ZIP and checksum paths.
It writes a lowercase SHA-256 followed by two spaces and the ZIP filename. It then expands the ZIP
into one generated directory under the system temporary directory, checks the same required product
files and single native module, recomputes the archive hash, verifies the checksum line, and removes
only that validated temporary directory.

### Archive evidence

The archive command was executed once:

```powershell
& .\scripts\create_windows_release.ps1 -InputDirectory .\dist\perfwatch -OutputDirectory .\release
```

| Evidence | Result |
| --- | --- |
| Command exit code | `0` |
| Archive | `perfwatch-0.1.0-windows-x64.zip` |
| Archive size | `40,374,135` bytes |
| SHA-256 | `1cdf2ad963a0a1bd170ffdc9569057b6deb0f65d426b7272fe2c0e8196d0290e` |
| Checksum file | `perfwatch-0.1.0-windows-x64.zip.sha256` |
| Extraction and required-layout check | PASS |

The checksum file records:

```text
1cdf2ad963a0a1bd170ffdc9569057b6deb0f65d426b7272fe2c0e8196d0290e  perfwatch-0.1.0-windows-x64.zip
```

### Distribution limitation

The ZIP is an unsigned Windows x64 archive. The SHA-256 file provides integrity verification, not
publisher identity or code-signing trust. No installer, signing system, upload, GitHub Release, or
other publication occurred in 8D; publication and documentation closeout remain 8E work.

## 8E — GitHub Release and Documentation Closeout

### Release automation

8E uses the owner-approved single scoped pass rather than the six-stage pipeline. The Windows-only
workflow reads version `0.1.0` from `python/pyproject.toml`, rejects non-semantic versions, and for a
tag run requires the exact tag `v0.1.0`. `build-windows` runs the existing 8C build/smoke and 8D
archive scripts on `windows-latest`, then uploads only the ZIP and checksum. Manual dispatch stops
after artifact upload.

The dependent `publish` job runs only after a successful pushed tag build. Only that job receives
`contents: write`; it uses the repository `GITHUB_TOKEN` and `gh release create`. No PAT, installer,
signing key, or updater was added. The workflow file must reach GitHub before it can run, and this
local implementation does not claim an unobserved workflow run or published Release.

### Phase 8 implementation commits

| Work item | Commit |
| --- | --- |
| 8A live Windows collection | `eac1db5b6d26f1de63201c83289356fec0ea0405` |
| 8B native Win32 Overlay | `1678a085882090acab852a9f25c09641ec39d091` |
| 8C Windows application assembly | `652d17f43aa0114ca9f6fbb8d6f2242452286418` |
| 8D ZIP and SHA-256 | `49d78b701363d39c6a20ecce3ec3f41205f64d7d` |

The earlier sections retain the actual 8A–8D commands and outcomes, validated MSVC/Ninja/Python/
pybind11 paths, PyInstaller 6.22.2 version, 88,274,952-byte directory bundle, 40,374,135-byte ZIP,
and SHA-256 `1cdf2ad963a0a1bd170ffdc9569057b6deb0f65d426b7272fe2c0e8196d0290e`.

### Local closeout evidence

8E ran only the approved static consistency group:

```powershell
python -c "from pathlib import Path; p=Path('.github/workflows/release.yml').read_text(encoding='utf-8'); required=('workflow_dispatch','windows-latest','contents: write','gh release create','create_windows_release.ps1'); assert all(value in p for value in required)"
rg -n "Phase 8|WindowsCollector|ctypes|PyInstaller 6.22.2|SHA-256|unsigned|Phase 9" perfwatch\README.md perfwatch\docs
git diff --check
```

All three commands exited with code zero. The first found every required workflow marker, the second
confirmed the Phase 8/9 terminology across project documentation, and the final check found no diff
errors (only Git's existing LF-to-CRLF working-copy notices). No application suite or remote GitHub
workflow was run for 8E.

### Remaining Phase 9 boundary

Phase 8 establishes implementation, package composition, one-machine capability, and local release
artifact integrity. Phase 9 retains physical sensor accuracy and stability, battery charge-state
behavior, Dashboard browser visuals, Overlay appearance/topmost/click-through/DPI behavior, and the
packaged live flow through collection, estimation, persistence, queries, WebSocket streaming,
Dashboard/Overlay display, shutdown, and restart.
