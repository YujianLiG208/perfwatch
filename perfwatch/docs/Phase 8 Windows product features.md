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
