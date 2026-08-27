# Phase 8 Windows Product Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver live Windows collection, a framework-free Win32 overlay, a PyInstaller directory-mode Windows application, a versioned ZIP with SHA-256, and GitHub Release automation without mixing mock values into failed live collection.

**Architecture:** Keep the existing collector-to-service data flow. A stateful C++ `WindowsCollector` produces nullable native measurements through pybind11; Python enriches and persists them; the Dashboard and a Python `ctypes` Win32 overlay consume the existing snapshot contract. A console product launcher assembles the service and overlay, and focused PowerShell/Python scripts build and verify the unsigned Windows artifact.

**Tech Stack:** C++17, Windows SDK 10.0.28000.0, PDH, Power API, PSAPI, pybind11 3.1.0, CMake 4.2.3, Ninja 1.13.2, MSVC 19.51, Python 3.12, FastAPI, Uvicorn, httpx, SQLite, React 19, TypeScript 6, Vite 8, PyInstaller 6.22.2, PowerShell 7, GitHub Actions.

**Spec:** [`docs/superpowers/specs/2026-08-24-phase-8-windows-product-features-design.md`](../specs/2026-08-24-phase-8-windows-product-features-design.md)

## Global Constraints

- Windows x64 is the only Phase 8 runtime, packaging, and release target.
- `PERFWATCH_USE_MOCK_COLLECTOR=true` or the package `--mock` switch is the only way to select mock data.
- Live failure returns missing data or an error; it never starts or merges a mock collector.
- Unavailable measurements are `null`/`None`/`std::nullopt` and render as `N/A` or `Unavailable`.
- CPU package power and temperature remain nullable on hardware without a trustworthy generic source.
- GPU vendor collection and process VRAM remain unavailable; add no GPU SDK.
- Overlay code uses only Python `ctypes`, User32/GDI, the standard library, and existing `httpx`.
- Add no Tkinter, Tcl/Tk, Qt, Electron, WebView2, installer, service, auto-update, or signing system.
- PyInstaller is pinned exactly to `6.22.2` in the packaging optional dependency.
- The only release platform is Windows x64 and the only release files are an unsigned ZIP and SHA-256 file.
- Keep tests minimal: one focused regression check per non-trivial boundary and one package smoke; do not repeat unrelated full suites at every work item.
- 8A, 8C, and 8D use the repository's risk-based six stages. 8B uses the default three stages. 8E retains the owner-approved scoped implementation/validation/diff/commit exception.
- Any environment or tooling failure stops the current stage without retry or tool substitution until the owner resolves it and explicitly resumes.

---

## Pipeline Classification

For 8A, 8C, and 8D: plan only; implement visibly; validate only; record durable evidence; review
the complete diff; commit or hand off. Stage 1 has the mandatory approval stop. Other boundaries
follow `AGENTS.md` and do not add automatic approval pauses.

For 8B: scope and assess risk; implement and verify iteratively; run the final gate, update durable
documentation, review the complete diff, and commit when already authorized.

Targeted RED/GREEN commands are permitted during Stage 2. Broader scoped commands belong only to Stage 3. Never combine a stage with the next stage.

Run local 8A–8D commands from the repository's `perfwatch` directory. Run 8E workflow and
repository-wide documentation commands from the repository root, where `.github` and `perfwatch`
are siblings.

## File Map

### Create

- `cpp/include/perfwatch/windows_collector.hpp` — public Windows collector, issue, and process-delta interfaces.
- `cpp/platform/windows/pdh_collector.hpp` — internal RAII PDH total-CPU counter.
- `cpp/tests/test_windows_collector.cpp` — one pure delta/tracker test file.
- `python/src/perfwatch/overlay/__init__.py` — overlay public entry points.
- `python/src/perfwatch/overlay/model.py` — immutable display model and nullable formatting.
- `python/src/perfwatch/overlay/win32.py` — User32/GDI window, HTTP worker, message loop, and shutdown.
- `python/src/perfwatch/overlay/__main__.py` — source-tree overlay CLI.
- `python/tests/test_overlay.py` — display-model checks and one Windows window-creation smoke.
- `python/src/perfwatch/runtime.py` — packaged product launcher and private overlay-child dispatch.
- `python/tests/test_runtime.py` — one parser/resource/child-command boundary test.
- `packaging/perfwatch.spec` — PyInstaller directory-mode bundle definition.
- `scripts/build_windows_package.ps1` — Dashboard/native/PyInstaller build coordinator.
- `scripts/smoke_windows_package.py` — packaged HTTP smoke and graceful console shutdown.
- `scripts/create_windows_release.ps1` — ZIP, extraction, and SHA-256 creation/verification.
- `.github/workflows/release.yml` — Windows build and tag-only publish workflow.
- `docs/Phase 8 Windows product features.md` — incremental 8A–8E process note.

### Modify

- `cpp/include/perfwatch/snapshot.hpp`
- `cpp/platform/windows/windows_collector.cpp`
- `cpp/platform/windows/pdh_collector.cpp`
- `cpp/bindings/pybind_module.cpp`
- `cpp/CMakeLists.txt`
- `cpp/tests/test_snapshot.cpp`
- `cpp/tests/test_mock_collector.cpp`
- `python/src/perfwatch/collectors/native.py`
- `python/src/perfwatch/api/service.py`
- `python/src/perfwatch/server.py`
- `python/src/perfwatch/analytics/snapshot.py`
- `python/pyproject.toml`
- `python/tests/test_mock_collector.py`
- `python/tests/test_service.py`
- `python/tests/test_server.py`
- `ui/dashboard/src/types.ts`
- `ui/dashboard/src/data.ts`
- `ui/dashboard/src/App.tsx`
- `ui/dashboard/src/components/ProcessTable.tsx`
- `ui/dashboard/src/test/fixtures.ts`
- `ui/dashboard/src/data.test.ts`
- `ui/dashboard/src/App.test.tsx`
- `.gitignore`
- `README.md`
- `docs/roadmap.md`
- `docs/architecture.md`
- `docs/data_model.md`
- `docs/testing_strategy.md`
- `docs/ci_cd.md`

### Delete

- `cpp/platform/windows/wmi_fallback.cpp` — unused placeholder; Phase 8 uses native power APIs and does not add a WMI layer.

---

## Task 1: Work Item 8A — Live Windows Collection

**Outcome:** The default Windows collector returns real, nullable CPU/memory/battery/process readings through pybind11; partial issues are recorded once, and missing native collection never falls back to mock.

**Commit:** `feat: collect live Windows metrics`

**Files:**
- Create: `cpp/include/perfwatch/windows_collector.hpp`
- Create: `cpp/platform/windows/pdh_collector.hpp`
- Create: `cpp/tests/test_windows_collector.cpp`
- Create in Stage 4: `docs/Phase 8 Windows product features.md`
- Modify: `cpp/include/perfwatch/snapshot.hpp`
- Modify: `cpp/platform/windows/windows_collector.cpp`
- Modify: `cpp/platform/windows/pdh_collector.cpp`
- Modify: `cpp/bindings/pybind_module.cpp`
- Modify: `cpp/CMakeLists.txt`
- Modify: `cpp/tests/test_snapshot.cpp`
- Modify: `cpp/tests/test_mock_collector.cpp`
- Delete: `cpp/platform/windows/wmi_fallback.cpp`
- Modify: `python/src/perfwatch/collectors/native.py`
- Modify: `python/src/perfwatch/api/service.py`
- Modify: `python/src/perfwatch/analytics/snapshot.py`
- Modify: `python/tests/test_mock_collector.py`
- Modify: `python/tests/test_service.py`
- Modify: `ui/dashboard/src/types.ts`
- Modify: `ui/dashboard/src/data.ts`
- Modify: `ui/dashboard/src/App.tsx`
- Modify: `ui/dashboard/src/components/ProcessTable.tsx`
- Modify: `ui/dashboard/src/test/fixtures.ts`
- Modify: `ui/dashboard/src/data.test.ts`
- Modify: `ui/dashboard/src/App.test.tsx`

**Interfaces:**
- Produces: `perfwatch::WindowsCollector::collect() -> SystemSnapshot`
- Produces: `perfwatch::WindowsCollector::collection_issues() -> const std::vector<CollectionIssue>&`
- Produces: native Python class `perfwatch_native.WindowsCollector` with `collect() -> dict[str, Any]`
- Produces: `NativeCollector.collect() -> dict[str, Any]`, raising `RuntimeError` if the Windows native class is absent.
- Produces: nullable API fields using existing keys; no endpoint changes.

### Stage 1 — Plan only

- [ ] Print this outcome, the exact 24-file 8A scope above, and the Stage 2 commands.
- [ ] Confirm `git status --short` contains no unreviewed implementation change.
- [ ] Confirm the validated Ninja, MSVC, Visual Studio shell, Python, and pybind11 paths recorded in the Phase 7 process note are still the owner-approved inputs; run no native command yet.
- [ ] Stop and request approval for 8A Stage 2.

### Stage 2 — Implement visibly

#### Step 2.1 — Write the single C++ delta/tracker RED check

- [ ] Add `test_windows_collector()` to `cpp/tests/test_windows_collector.cpp` and call it from the existing `perfwatch_cpp_tests` main:

```cpp
#include <cassert>

#include "perfwatch/windows_collector.hpp"

void test_windows_collector() {
    perfwatch::ProcessCpuTracker tracker;
    const perfwatch::ProcessCpuReading first{42, 100, 1'000};
    const perfwatch::ProcessCpuReading second{42, 100, 5'001'000};
    const perfwatch::ProcessCpuReading reused{42, 200, 6'001'000};

    assert(!tracker.update(first, 10'000'000, 2).has_value());
    const auto usage = tracker.update(second, 20'000'000, 2);
    assert(usage.has_value());
    assert(*usage == 25.0);
    assert(!tracker.update(second, 20'000'000, 2).has_value());
    assert(!tracker.update(reused, 30'000'000, 2).has_value());
}
```

- [ ] Load the owner-validated Visual Studio environment, configure the ignored Phase 8 build
  directory, then build only the C++ test target and confirm RED because `windows_collector.hpp`
  and `ProcessCpuTracker` do not exist:

```powershell
& 'C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\Launch-VsDevShell.ps1' -Arch amd64 -HostArch amd64
cmake -S cpp -B build\phase8 -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_MAKE_PROGRAM='C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe' -DPython3_EXECUTABLE='C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -Dpybind11_DIR='C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages\pybind11\share\cmake\pybind11'
cmake --build build\phase8 --target perfwatch_cpp_tests
```

Expected: compilation failure naming the missing Windows collector header or types.

#### Step 2.2 — Add nullable native types and process tracking

- [ ] Change only measurements that can be absent in `snapshot.hpp` to optionals:

```cpp
#include <optional>

struct CpuSample {
    std::optional<double> usage_percent;
    std::optional<double> frequency_mhz;
    std::optional<double> package_power_watts;
    std::optional<double> temperature_celsius;
};

struct MemorySample {
    std::optional<std::uint64_t> total_bytes;
    std::optional<std::uint64_t> used_bytes;
};

struct BatterySample {
    bool available;
    std::optional<bool> charging;
    std::optional<double> percent;
    std::optional<double> power_watts;
    std::optional<double> energy_remaining_wh;
};
```

- [ ] Apply the same rule to GPU numeric measurements and process `cpu_percent`, `rss_bytes`, `vram_bytes`, and `estimated_power_score`; retain required PID/name and availability/vendor fields.
- [ ] Create `windows_collector.hpp` with these exact public contracts:

```cpp
struct CollectionIssue {
    std::string code;
    std::string message;
};

struct ProcessCpuReading {
    std::uint32_t pid;
    std::uint64_t creation_time_100ns;
    std::uint64_t cpu_time_100ns;
};

class ProcessCpuTracker {
public:
    std::optional<double> update(
        const ProcessCpuReading& reading,
        std::uint64_t wall_time_100ns,
        std::uint32_t logical_processors
    );
    void retain(const std::vector<std::uint32_t>& active_pids);

private:
    struct Baseline {
        std::uint64_t creation_time_100ns;
        std::uint64_t cpu_time_100ns;
        std::uint64_t wall_time_100ns;
    };
    std::map<std::uint32_t, Baseline> baselines_;
};

class WindowsCollector final : public Collector {
public:
    WindowsCollector();
    ~WindowsCollector() override;
    WindowsCollector(WindowsCollector&&) noexcept;
    WindowsCollector& operator=(WindowsCollector&&) noexcept;
    SystemSnapshot collect() override;
    const std::vector<CollectionIssue>& collection_issues() const;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
```

- [ ] Implement `ProcessCpuTracker::update()` with exact guards: return empty for processor count zero, new PID, changed creation time, non-increasing CPU time, or non-increasing wall time; otherwise return the clamped percentage:

```cpp
const auto cpu_delta = reading.cpu_time_100ns - previous.cpu_time_100ns;
const auto wall_delta = wall_time_100ns - previous.wall_time_100ns;
const auto percent = 100.0 * static_cast<double>(cpu_delta) /
    (static_cast<double>(wall_delta) * logical_processors);
return std::clamp(percent, 0.0, 100.0);
```

- [ ] Implement `retain()` by erasing every baseline whose PID is absent from the current sample;
  call it after each completed process enumeration so exited processes cannot grow the map.

- [ ] Update existing C++ mock assertions to use `.value()` where mock optionals are known to be populated.
- [ ] Run only `cmake --build build\phase8 --target perfwatch_cpp_tests`; expected GREEN for the pure tracker check before live API wiring.

#### Step 2.3 — Implement the Windows SDK sources

- [ ] Implement `PdhCpuCounter` in `pdh_collector.hpp/.cpp` as a non-copyable RAII object that calls `PdhOpenQueryW`, `PdhAddEnglishCounterW(L"\\Processor(_Total)\\% Processor Time")`, `PdhCollectQueryData`, `PdhGetFormattedCounterValue(PDH_FMT_DOUBLE)`, and `PdhCloseQuery`. The first successful collection returns empty; later valid values are clamped to `0..100`.
- [ ] Implement `WindowsCollector::Impl` in `windows_collector.cpp` with one PDH counter, one `ProcessCpuTracker`, and one per-sample `std::vector<CollectionIssue>`.
- [ ] Use `std::chrono::system_clock` for `timestamp_ms` and `GetSystemTimeAsFileTime` for the shared 100-nanosecond process-delta wall clock.
- [ ] Populate memory with this exact validity rule:

```cpp
MEMORYSTATUSEX status{sizeof(status)};
if (GlobalMemoryStatusEx(&status)) {
    snapshot.memory.total_bytes = status.ullTotalPhys;
    snapshot.memory.used_bytes = status.ullTotalPhys - status.ullAvailPhys;
} else {
    issues.push_back({"memory_unavailable", "GlobalMemoryStatusEx failed"});
}
```

- [ ] Populate frequency from `CallNtPowerInformation(ProcessorInformation, ...)`, averaging only positive `CurrentMhz` values. Leave package power and temperature empty and emit each stable capability issue once through the binding/service path.
- [ ] Populate battery from `GetSystemPowerStatus` and `CallNtPowerInformation(SystemBatteryState, ...)`: set `available=false` with nullable values when no battery exists; accept percentage only in `0..100`; convert valid remaining capacity from mWh to Wh and absolute discharge rate from mW to W; never infer a value from zero or an unknown sentinel.
- [ ] Enumerate PIDs with `EnumProcesses`; open with least required query rights; read creation/kernel/user times, executable name, and working set; skip access-denied or exited processes; use `ProcessCpuTracker`, call `retain()` with the enumerated PIDs, sort valid processes by CPU descending then RSS descending, and keep ten.
- [ ] Set GPU `available=false`, vendor `unavailable`, and all GPU numeric values empty. Set process VRAM empty and initial estimated score empty; Python enrichment owns the estimate.
- [ ] On non-Windows builds, keep `WindowsCollector::collect()` compile-safe and throw `PerfwatchError("live Windows collection is unavailable on this platform")`.
- [ ] Remove `wmi_fallback.cpp`; remove it from CMake; add `test_windows_collector.cpp`; under `if(WIN32)` link `pdh`, `powrprof`, and `psapi`.
- [ ] Run only `cmake --build build\phase8 --target perfwatch_cpp_tests`; expected GREEN.

#### Step 2.4 — Bind the live class and remove Python mock fallback

- [ ] Keep `get_mock_snapshot()` for explicit deterministic tests and add this Windows-only class binding:

```cpp
py::class_<perfwatch::WindowsCollector>(module, "WindowsCollector")
    .def(py::init<>())
    .def("collect", [](perfwatch::WindowsCollector& collector) {
        auto result = snapshot_to_dict(collector.collect());
        py::list issues;
        for (const auto& issue : collector.collection_issues()) {
            py::dict value;
            value["code"] = issue.code;
            value["message"] = issue.message;
            issues.append(value);
        }
        result["_collection_issues"] = issues;
        return result;
    });
```

- [ ] Replace the native Python wrapper with a stateful live-class wrapper. Import failure must be stored and raised on `collect()`, never delegated to `get_python_mock_snapshot`:

```python
class NativeCollector:
    def __init__(self) -> None:
        try:
            from perfwatch_native import WindowsCollector
        except (ImportError, AttributeError) as error:
            self._collector = None
            self._import_error = error
        else:
            self._collector = WindowsCollector()
            self._import_error = None

    def collect(self) -> dict[str, Any]:
        if self._collector is None:
            raise RuntimeError(
                "live Windows collector unavailable; explicitly enable mock mode for tests"
            ) from self._import_error
        return self._collector.collect()
```

- [ ] Keep `get_snapshot()` as a no-argument one-shot compatibility helper implemented by `NativeCollector().collect()`; remove the live-path sample index.
- [ ] Replace the fallback test in `test_mock_collector.py` with one check that a missing extension raises `RuntimeError` and make the fake module expose a fake `WindowsCollector` class.
- [ ] Run only `python -m pytest python/tests/test_mock_collector.py -q`; expected GREEN and no fallback assertion.

#### Step 2.5 — Strip and deduplicate native issues at the service boundary

- [ ] Add one `IssueCollector` and one test to `test_service.py` that calls `sample_once()` twice, then asserts one event was recorded and `_collection_issues` is absent from both `current_snapshot` and persisted snapshots:

```python
class IssueCollector:
    def collect(self) -> dict[str, Any]:
        snapshot = deepcopy(get_mock_snapshot())
        snapshot["_collection_issues"] = [
            {"code": "cpu_power_unavailable", "message": "package power is unavailable"}
        ]
        return snapshot


def test_collection_issues_are_removed_and_recorded_once(tmp_path) -> None:
    async def exercise() -> None:
        repository = RecordingRepository()
        service = ServiceState(
            settings=Settings(database_path=tmp_path / "issues.sqlite3"),
            collector=IssueCollector(),
            repository=repository,
        )
        await service.sample_once()
        await service.sample_once()

        assert len(repository.events) == 1
        assert repository.events[0]["source"] == "collector"
        assert all("_collection_issues" not in item for item in repository.snapshots)
        assert "_collection_issues" not in service.current_snapshot

    asyncio.run(exercise())
```

- [ ] Add `_reported_collection_issues: set[str]` to `ServiceState`; immediately pop the reserved list after collection; accept only mapping items with non-empty string `code` and `message`; record the first occurrence as level `warning`; never persist or publish the reserved key.
- [ ] Generalize event writing to `_record_event(level, source, message)` and keep `_record_error()` as the exception-formatting wrapper.
- [ ] In `analytics/snapshot.py`, keep raw `vram_bytes=None` but calculate the relative estimate from valid CPU/RSS using a zero VRAM contribution:

```python
process["estimated_power_score"] = (
    estimate_process_power_score(cpu, rss, 0 if vram is None else vram)
    if cpu is not None and cpu >= 0 and rss is not None
    else None
)
```

- [ ] Run only `python -m pytest python/tests/test_service.py python/tests/test_snapshot_enrichment.py -q`; expected GREEN.

#### Step 2.6 — Make the Dashboard nullable without redesigning it

- [ ] Change measurable numeric fields in `CpuMetrics`, `MemoryMetrics`, `BatteryMetrics`, `GpuMetrics`, `ProcessSample`, and `MetricSample` to `number | null`; change battery `charging` to `boolean | null`.
- [ ] Centralize nullable presentation:

```ts
export function formatPercent(value: number | null): string {
  return value === null || !Number.isFinite(value) ? "Unavailable" : `${value.toFixed(1)}%`;
}

export function formatBytes(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "Unavailable";
  if (value <= 0) return "0 B";
  // retain the existing unit scaling below
}

export function formatWatts(value: number | null): string {
  return value === null || !Number.isFinite(value) ? "Unavailable" : `${value.toFixed(1)} W`;
}
```

- [ ] Make `snapshotToMetricSample()` return `null` for memory percentage unless total and used bytes are both non-null and total is positive. Preserve nullable power and battery points so Recharts omits them.
- [ ] Replace direct `.toFixed()` and arithmetic in `App.tsx`/`ProcessTable.tsx` with the shared formatters. Keep current layout and copy except unavailable values.
- [ ] Add one nullable fixture assertion to `data.test.ts` and one App assertion that null CPU power/temperature/battery power displays `Unavailable`; do not add component-by-component duplicates.
- [ ] Run only `npm.cmd test -- src/data.test.ts src/App.test.tsx` from `ui/dashboard`; expected GREEN.
- [ ] Stop and request approval for 8A Stage 3.

### Stage 3 — Validate only

- [ ] Run the scoped Python checks once:

```powershell
python -m pytest python/tests/test_mock_collector.py python/tests/test_service.py python/tests/test_snapshot_enrichment.py python/tests/test_sqlite_writer.py -q
python -m ruff check python/src/perfwatch/collectors python/src/perfwatch/api/service.py python/src/perfwatch/analytics/snapshot.py python/tests/test_mock_collector.py python/tests/test_service.py
```

- [ ] Run the scoped frontend checks once from `ui/dashboard`:

```powershell
npm.cmd test -- src/data.test.ts src/App.test.tsx
npm.cmd run build
```

- [ ] Before the native command, print the exact owner-validated paths. Load the Visual Studio environment and run one configure/build/CTest/native-smoke group:

```powershell
& 'C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\Launch-VsDevShell.ps1' -Arch amd64 -HostArch amd64
cmake -S cpp -B build\phase8 -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_MAKE_PROGRAM='C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe' -DPython3_EXECUTABLE='C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -Dpybind11_DIR='C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages\pybind11\share\cmake\pybind11'
cmake --build build\phase8
ctest --test-dir build\phase8 --output-on-failure
$env:PYTHONPATH = "$PWD\build\phase8;$PWD\python\src"
python -c "from perfwatch.collectors.native import NativeCollector; c=NativeCollector(); a=c.collect(); b=c.collect(); assert a['timestamp_ms'] <= b['timestamp_ms']; assert a['timestamp_ms'] != 1710000000000; print(a['cpu'], a['memory'], a['battery'], len(a['top_processes']))"
```

- [ ] Report PASS/FAIL for each command. Do not run the complete Python or frontend suite again.
- [ ] Stop and request approval for 8A Stage 4.

### Stage 4 — Update process note

- [ ] Create `docs/Phase 8 Windows product features.md` with an 8A section containing changed interfaces, exact commands/exit codes/counts, actual tool paths, observed nullable hardware capabilities, and the Phase 9 accuracy limitation.
- [ ] Record that missing live collection never selected mock and that no GPU adapter was added.
- [ ] Stop and request approval for 8A Stage 5.

### Stage 5 — Review Git diff

- [ ] Run `git diff --check` and inspect the complete 8A diff.
- [ ] Confirm no `build/phase8/`, `dist/`, database, compiled extension, hardware identifier, absolute machine path, or secret is staged.
- [ ] Confirm only the 8A files and process note changed; report the diff summary.
- [ ] Stop and request approval for 8A Stage 6.

### Stage 6 — Commit

- [ ] Stage only reviewed 8A files and commit:

```powershell
git commit -m "feat: collect live Windows metrics"
```

- [ ] Show the commit identifier and `git status --short --branch`; stop.

---

## Task 2: Work Item 8B — Native Win32 Overlay

**Outcome:** A topmost, click-through, framework-free Win32 overlay consumes the existing snapshot endpoint and visibly distinguishes waiting, live, stale, and unavailable states.

**Commit:** `feat: add native Windows overlay`

**Files:**
- Create: `python/src/perfwatch/overlay/__init__.py`
- Create: `python/src/perfwatch/overlay/model.py`
- Create: `python/src/perfwatch/overlay/win32.py`
- Create: `python/src/perfwatch/overlay/__main__.py`
- Create: `python/tests/test_overlay.py`
- Modify: `python/pyproject.toml`
- Modify in Stage 3: `docs/Phase 8 Windows product features.md`

**Interfaces:**
- Produces: `OverlayModel(lines: tuple[str, ...], status: Literal["waiting", "live", "stale"])`
- Produces: `model_from_snapshot(snapshot: Mapping[str, Any]) -> OverlayModel`
- Produces: `stale_model(previous: OverlayModel | None) -> OverlayModel`
- Produces: `Win32OverlayWindow.create() -> int`, `run() -> None`, and `close() -> None`
- Produces: `run_overlay(snapshot_url: str, interval_seconds: float, parent_pid: int | None) -> None`
- Produces console script: `perfwatch-overlay`

### Stage 1 — Scope and assess risk

- [ ] Print the seven-file 8B scope, exact targeted commands, and explicit exclusions: no Tk/Qt/tray/settings/theme/animation.
- [ ] Confirm the 8A commit exists and status is clean.
- [ ] Confirm no six-stage trigger applies, then continue unless a stop condition is found.

### Stage 2 — Implement and verify iteratively

#### Step 2.1 — Write one display-model RED test

- [ ] Create `test_overlay.py` with one parameter-light test covering live/null/stale states:

```python
def test_overlay_models_live_unavailable_and_stale_states() -> None:
    snapshot = deepcopy(get_mock_snapshot())
    snapshot["cpu"]["package_power_watts"] = None
    snapshot["battery"]["estimated_remaining_seconds"] = None
    live = model_from_snapshot(snapshot)

    assert live.status == "live"
    assert "CPU 42.5%" in live.lines[0]
    assert any("Power N/A" in line for line in live.lines)
    assert any("Battery 78.0%" in line for line in live.lines)

    waiting = stale_model(None)
    assert waiting.status == "waiting"
    assert waiting.lines == ("Waiting for service",)

    stale = stale_model(live)
    assert stale.status == "stale"
    assert stale.lines[-1] == "STALE"
```

- [ ] Run only `python -m pytest python/tests/test_overlay.py -q`; expected RED because the overlay package does not exist.

#### Step 2.2 — Implement the immutable display model

- [ ] Implement `OverlayModel`, `_percent`, `_bytes`, `_watts`, `_duration`, `model_from_snapshot`, and `stale_model` in `model.py`. Each formatter must accept missing keys, `None`, booleans, non-finite values, and wrong types and return `N/A` rather than raising.
- [ ] Limit the model to these lines: CPU usage/frequency, memory used/total, battery/remaining time, CPU/battery power, highest-load process, and status.
- [ ] Export only `OverlayModel`, `model_from_snapshot`, `stale_model`, and `run_overlay` from `overlay/__init__.py`.
- [ ] Run only `python -m pytest python/tests/test_overlay.py -q`; expected GREEN for model behavior.

#### Step 2.3 — Implement one Win32 window and one HTTP worker

- [ ] Define only the required Win32 structures/callbacks in `win32.py`: `WNDCLASSW`, `PAINTSTRUCT`, `RECT`, `WNDPROC`, `RegisterClassW`, `CreateWindowExW`, `SetLayeredWindowAttributes`, `SetWindowPos`, `BeginPaint`, `DrawTextW`, `EndPaint`, `PostMessageW`, `GetMessageW`, `DispatchMessageW`, and `DestroyWindow`.
- [ ] Keep `win32.py` import-safe on non-Windows: define the public names without loading a WinDLL at import time and raise `RuntimeError("Win32 overlay requires Windows")` only when `create()` or `run_overlay()` is called. This lets Ubuntu CI collect the skipped smoke test.
- [ ] Use these exact style rules:

```python
extended_style = (
    WS_EX_LAYERED
    | WS_EX_TOPMOST
    | WS_EX_TOOLWINDOW
    | WS_EX_NOACTIVATE
    | WS_EX_TRANSPARENT
)
window_style = WS_POPUP
```

- [ ] Return `HTTRANSPARENT` from `WM_NCHITTEST`; redraw on one private `WM_APP + 1` message; paint a semi-transparent dark rectangle and Segoe UI text; position a fixed compact window at the top-right of `SPI_GETWORKAREA`.
- [ ] `Win32OverlayWindow.create()` registers the class and creates the HWND without starting network work. `close()` posts `WM_CLOSE`; `run()` owns the message loop and deletes GDI objects in `finally`.
- [ ] Start one daemon worker in `run_overlay()`. Use `httpx.Client(timeout=0.5)` and `stop_event.wait(interval_seconds)`; after a successful `raise_for_status()/json()` publish `model_from_snapshot`; after `httpx.HTTPError`, invalid JSON, or invalid snapshot publish `stale_model(previous)`; notify only with `PostMessageW`.
- [ ] If `parent_pid` is supplied, use `OpenProcess(SYNCHRONIZE, ...)` and exit when the parent handle is signaled. Source execution installs a SIGINT handler that posts `WM_CLOSE`.
- [ ] Add `__main__.py` arguments `--snapshot-url`, `--interval-seconds`, and `--parent-pid`; add `perfwatch-overlay = "perfwatch.overlay.__main__:main"` to `pyproject.toml`.

#### Step 2.4 — Add one real window smoke to the same test file

- [ ] Add one Windows-only test that calls `create()`, asserts a nonzero HWND, and closes it in `finally`; skip only when `sys.platform != "win32"`. Do not mock every Win32 function.
- [ ] Run only `python -m pytest python/tests/test_overlay.py -q`; expected GREEN with model checks and one window smoke.
- [ ] Run only `python -m ruff check python/src/perfwatch/overlay python/tests/test_overlay.py`; expected GREEN.
- [ ] Continue to the final gate when the focused checks are green.

### Stage 3 — Run final gate and review

- [ ] Run exactly once:

```powershell
python -m pytest python/tests/test_overlay.py -q
python -m ruff check python/src/perfwatch/overlay python/tests/test_overlay.py
```

- [ ] Report test count and the Windows smoke result. Do not run the full Python suite and do not perform visual acceptance.
- [ ] Append 8B interfaces, exact validation evidence, the no-GUI-framework decision, and the Phase 9 visual/click-through/DPI boundary to the process note.
- [ ] Run `git diff --check`; inspect the complete seven-file 8B diff and process-note delta.
- [ ] Confirm no screenshots, GUI dependencies, generated bytecode, databases, or build output are included.
- [ ] Commit only reviewed 8B files:

```powershell
git commit -m "feat: add native Windows overlay"
```

- [ ] Show commit identifier and clean status.

---

## Task 3: Work Item 8C — Windows Directory-Mode Runtime

**Outcome:** One console `perfwatch.exe` starts the local service and overlay, uses LocalAppData for mutable data, and ships all required assets in a PyInstaller 6.22.2 directory.

**Commit:** `build: assemble Windows application`

**Files:**
- Create: `python/src/perfwatch/runtime.py`
- Create: `python/tests/test_runtime.py`
- Create: `packaging/perfwatch.spec`
- Create: `scripts/build_windows_package.ps1`
- Create: `scripts/smoke_windows_package.py`
- Modify: `python/src/perfwatch/server.py`
- Modify: `python/tests/test_server.py`
- Modify: `python/pyproject.toml`
- Modify in Stage 4: `docs/Phase 8 Windows product features.md`

**Interfaces:**
- Produces: `bundle_root() -> Path`, `default_data_directory() -> Path`, and `self_command() -> list[str]`
- Produces: public arguments `--host`, `--port`, `--database-path`, `--dashboard-directory`, `--mock`, and `--no-overlay`
- Produces: private arguments `--overlay-child`, `--snapshot-url`, and `--parent-pid`
- Produces: `scripts/build_windows_package.ps1 -NinjaPath 'C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe' -VsDevShellPath 'C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\Launch-VsDevShell.ps1' -PythonPath 'C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'`
- Produces: `dist/perfwatch/perfwatch.exe`

### Stage 1 — Plan only

- [ ] Print the nine-file 8C scope and exact build/smoke commands.
- [ ] Confirm 8A/8B commits exist, the Dashboard lockfile exists, PyInstaller reports 6.22.2, and status is clean. These checks must not build.
- [ ] Stop and request approval for 8C Stage 2.

### Stage 2 — Implement visibly

#### Step 2.1 — Write one runtime-boundary RED test

- [ ] Create `test_runtime.py` with one focused test for LocalAppData, frozen resource root, and child command:

```python
def test_runtime_paths_and_frozen_child_command(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(runtime.sys, "frozen", True, raising=False)
    monkeypatch.setattr(runtime.sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setattr(runtime.sys, "executable", str(tmp_path / "perfwatch.exe"))

    assert runtime.default_data_directory() == tmp_path / "PerfWatch"
    assert runtime.bundle_root() == tmp_path / "bundle"
    assert runtime.self_command() == [str(tmp_path / "perfwatch.exe")]
```

- [ ] Run only `python -m pytest python/tests/test_runtime.py -q`; expected RED because `runtime.py` does not exist.

#### Step 2.2 — Implement frozen/source paths and launcher arguments

- [ ] Implement the exact path rules:

```python
def bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[3]


def default_data_directory() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA is required for the packaged Windows runtime")
    return Path(local_app_data) / "PerfWatch"


def self_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [sys.executable, "-m", "perfwatch.runtime"]
```

- [ ] Make `server.default_dashboard_directory()` return `bundle_root()/"dashboard"` when frozen and retain the existing source-tree path otherwise.
- [ ] Build one parser with the approved public and private arguments. `--mock` defaults false; `--no-overlay` defaults false; private child mode delegates directly to `run_overlay()` and returns.
- [ ] Run only `python -m pytest python/tests/test_runtime.py python/tests/test_server.py -q`; expected GREEN.

#### Step 2.3 — Implement coordinated service/overlay lifetime

- [ ] In normal mode, create the data directory, construct `Settings(database_path=..., use_mock_collector=args.mock)`, create the app with the resolved Dashboard path, and run `uvicorn.Server` in one non-daemon thread.
- [ ] Poll `GET /health`, `GET /snapshot`, and `/` with a shared five-second deadline. A 503 snapshot in live mode keeps polling; deadline expiry sets `server.should_exit=True`, joins, and exits nonzero with the last error. Mock mode follows the same readiness check.
- [ ] Unless `--no-overlay`, start `self_command() + ["--overlay-child", "--snapshot-url", snapshot_url, "--parent-pid", str(os.getpid())]`.
- [ ] Wait in the main console thread. On `KeyboardInterrupt`, set `server.should_exit=True`, terminate/wait the overlay with a five-second timeout, kill only if it does not exit, and join the server. Return nonzero if startup or a child exits unexpectedly.
- [ ] Keep existing `perfwatch-server` behavior and tests unchanged except for the shared frozen Dashboard path helper.

#### Step 2.4 — Define the PyInstaller bundle

- [ ] Add packaging extras exactly:

```toml
packaging = [
    "pyinstaller==6.22.2",
    "pybind11",
]
```

- [ ] Create `packaging/perfwatch.spec` using `python/src/perfwatch/runtime.py` as the entry script, `python/src` as `pathex`, `perfwatch_native` as a hidden import and binary, Dashboard `dist` as `dashboard`, and the package schema as `perfwatch/storage/schema.sql`.
- [ ] Build a console EXE named `perfwatch`, use PyInstaller's `_internal` contents directory, and copy README/LICENSE to the product root in the PowerShell build script rather than duplicating them inside `_internal`.
- [ ] `build_windows_package.ps1` must accept mandatory validated Ninja and Visual Studio shell paths plus a default current Python path; verify each path; load the VS shell once; derive pybind11 CMake directory from that Python; run Dashboard build, CMake Release configure/build, PyInstaller, and README/LICENSE copies in that order.
- [ ] The script must remove only the explicit project-owned `dist/perfwatch` and PyInstaller work directories after resolving them under the repository root; it must never delete a computed path outside the repository.

#### Step 2.5 — Add one package smoke script

- [ ] `smoke_windows_package.py` chooses an unused loopback port with a temporary bound socket,
  starts `dist/perfwatch/perfwatch.exe --mock --no-overlay --port PORT` with
  `CREATE_NEW_PROCESS_GROUP`, polls `/health`, `/snapshot`, and `/`, asserts HTTP 200, asserts the
  snapshot timestamp equals the explicit mock baseline, sends `signal.CTRL_BREAK_EVENT`, waits ten
  seconds, and fails if the exit code is nonzero or the process remains alive.
- [ ] The script accepts `--executable`, `--host`, and `--timeout`; it uses only Python standard
  library HTTP/socket/process modules.
- [ ] Run the targeted runtime tests only; do not build the package during Stage 2:

```powershell
python -m pytest python/tests/test_runtime.py python/tests/test_server.py -q
python -m ruff check python/src/perfwatch/runtime.py python/src/perfwatch/server.py python/tests/test_runtime.py scripts/smoke_windows_package.py
```

- [ ] Stop and request approval for 8C Stage 3.

### Stage 3 — Validate only

- [ ] Run the product build once with the owner-validated local paths:

```powershell
& .\scripts\build_windows_package.ps1 -NinjaPath 'C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe' -VsDevShellPath 'C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\Launch-VsDevShell.ps1' -PythonPath 'C:\Users\Yujian Li\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
python .\scripts\smoke_windows_package.py --executable .\dist\perfwatch\perfwatch.exe
```

- [ ] Inspect the directory once and assert the product root has `perfwatch.exe`, README, and LICENSE; `_internal` has `perfwatch_native*.pyd`, `dashboard/index.html`, and `perfwatch/storage/schema.sql`.
- [ ] Report PASS/FAIL, elapsed build time, bundle size, endpoint results, and clean shutdown. Do not rerun 8A/8B suites.
- [ ] Stop and request approval for 8C Stage 4.

### Stage 4 — Update process note

- [ ] Append the exact PyInstaller version, build command, output layout, bundle size, smoke results, and unsigned/no-installer boundary to the process note.
- [ ] Stop and request approval for 8C Stage 5.

### Stage 5 — Review Git diff

- [ ] Run `git diff --check`; inspect all 8C source/script/spec/process-note changes.
- [ ] Confirm `dist/`, `build/phase8/`, PyInstaller work output, `.pyd`, database, logs, and absolute tool paths are untracked and unstaged.
- [ ] Stop and request approval for 8C Stage 6.

### Stage 6 — Commit

- [ ] Commit reviewed 8C source and process-note files:

```powershell
git commit -m "build: assemble Windows application"
```

- [ ] Show commit identifier and clean status; stop.

---

## Task 4: Work Item 8D — ZIP and SHA-256

**Outcome:** The already validated directory bundle is archived once as `perfwatch-0.1.0-windows-x64.zip` with a verified SHA-256 file.

**Commit:** `build: package Windows release artifact`

**Files:**
- Create: `scripts/create_windows_release.ps1`
- Modify: `.gitignore`
- Modify in Stage 4: `docs/Phase 8 Windows product features.md`

**Interfaces:**
- Consumes: `dist/perfwatch/` from 8C.
- Produces: `release/perfwatch-0.1.0-windows-x64.zip`
- Produces: `release/perfwatch-0.1.0-windows-x64.zip.sha256`

### Stage 1 — Plan only

- [ ] Print the three-file 8D scope and archive-validation command.
- [ ] Confirm the 8C commit exists, `dist/perfwatch` is the previously validated directory, and project version is `0.1.0`; do not rebuild it.
- [ ] Stop and request approval for 8D Stage 2.

### Stage 2 — Implement visibly

- [ ] Add `release/` to `.gitignore`.
- [ ] Create `create_windows_release.ps1` with `-InputDirectory` defaulting to `dist/perfwatch` and `-OutputDirectory` defaulting to `release`.
- [ ] Read the version with this standard-library command and reject empty/non-semantic output:

```powershell
$version = & python -c "import pathlib,tomllib; print(tomllib.loads(pathlib.Path('python/pyproject.toml').read_text(encoding='utf-8'))['project']['version'])"
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw "project version is not semantic: $version" }
```

- [ ] Resolve the input/output paths and require input to remain under the repository root. Require `perfwatch.exe`, README, LICENSE, `_internal/dashboard/index.html`, `_internal/perfwatch/storage/schema.sql`, and one `_internal/perfwatch_native*.pyd`.
- [ ] Create the exact archive/checksum paths from `$version`; remove only existing files at those exact paths; call `Compress-Archive -Path $InputDirectory -DestinationPath $archivePath`.
- [ ] Write lowercase SHA-256 in two-space filename form using ASCII encoding:

```powershell
$hash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath $checksumPath -Value "$hash  $([IO.Path]::GetFileName($archivePath))" -Encoding ascii
```

- [ ] Create one temporary directory under `[IO.Path]::GetTempPath()`, expand the ZIP, assert the same required files under `$temporaryDirectory\perfwatch`, recompute and compare the hash, and remove only that validated temporary directory in `finally`.
- [ ] Run no application or test command in Stage 2; inspect script syntax and stop for approval for 8D Stage 3.

### Stage 3 — Validate only

- [ ] Run exactly once:

```powershell
& .\scripts\create_windows_release.ps1 -InputDirectory .\dist\perfwatch -OutputDirectory .\release
```

- [ ] Report archive name, byte size, SHA-256 value, extraction checks, and PASS/FAIL. Do not rebuild or rerun application tests.
- [ ] Stop and request approval for 8D Stage 4.

### Stage 4 — Update process note

- [ ] Append the exact archive/checksum names, size, hash, command, exit code, extraction result, and unsigned limitation.
- [ ] Stop and request approval for 8D Stage 5.

### Stage 5 — Review Git diff

- [ ] Run `git diff --check`; inspect only script, `.gitignore`, and process-note changes.
- [ ] Confirm `release/` and both generated release files are ignored and unstaged.
- [ ] Stop and request approval for 8D Stage 6.

### Stage 6 — Commit

- [ ] Commit reviewed 8D files:

```powershell
git commit -m "build: package Windows release artifact"
```

- [ ] Show commit identifier and clean status; stop.

---

## Task 5: Work Item 8E — GitHub Release and Documentation Closeout

**Outcome:** A Windows-only release workflow builds and publishes the approved ZIP/checksum from exact version tags, and documentation records verified Phase 8 behavior without repeating unrelated tests.

**Commit:** `ci: publish Windows releases`

**Process exception:** Execute this task as one visible scoped pass. It does not use the six separate stages.

**Files:**
- Create: `.github/workflows/release.yml`
- Modify: `README.md`
- Modify: `docs/roadmap.md`
- Modify: `docs/architecture.md`
- Modify: `docs/data_model.md`
- Modify: `docs/testing_strategy.md`
- Modify: `docs/ci_cd.md`
- Modify: `docs/Phase 8 Windows product features.md`

**Interfaces:**
- Trigger: pushed tags matching `v*.*.*` and manual `workflow_dispatch`.
- Publish gate: exact `vMAJOR.MINOR.PATCH` tag equal to `python/pyproject.toml` version.
- Release files: `perfwatch-0.1.0-windows-x64.zip` and `.zip.sha256`.

- [ ] Add a `build-windows` job on `windows-latest` with workflow-level `contents: read`,
  `actions/checkout@v7`, `actions/setup-python@v7` for Python 3.12, `actions/setup-node@v7` for Node
  24, `actions/upload-artifact@v4`, `npm ci`, packaging dependency installation, the 8C build
  script, package smoke, and the 8D archive script. Set build command working directory to
  `perfwatch`.
- [ ] In the Windows build job, locate Visual Studio with the runner's `vswhere.exe`, derive
  `Common7\Tools\Launch-VsDevShell.ps1`, resolve Ninja with `Get-Command ninja`, and pass those
  values plus `(Get-Command python).Source` to `scripts/build_windows_package.ps1`; fail immediately
  if any resolved path is empty.
- [ ] Validate tag input before building. On a tag event, require `^v\d+\.\d+\.\d+$` and
  equality with `v` plus the `pyproject.toml` version. Manual dispatch reads the project version but
  never publishes. Give the version step `id: version`, write `version=$version` to
  `$env:GITHUB_OUTPUT`, and expose it as the `build-windows` job output named `version`.
- [ ] Upload only the ZIP and checksum with `actions/upload-artifact`; do not upload the directory bundle.
- [ ] Add a separate `publish` job that depends on `build-windows`, runs only on a valid pushed tag,
  grants only that job `contents: write`, uses `actions/download-artifact@v4`, downloads into
  `perfwatch/release`, sets job environment `PROJECT_VERSION` to
  `${{ needs.build-windows.outputs.version }}`, and runs this version-derived command from the
  repository root:

```powershell
$archive = ".\perfwatch\release\perfwatch-$env:PROJECT_VERSION-windows-x64.zip"
gh release create $env:GITHUB_REF_NAME `
  $archive `
  "$archive.sha256" `
  --title "PerfWatch $env:GITHUB_REF_NAME" `
  --generate-notes `
  --notes "Unsigned Windows x64 archive. Verify the accompanying SHA-256 file before running."
```

- [ ] Keep the repository `GITHUB_TOKEN`; add no PAT or signing secret. A build/smoke/archive failure must prevent the publish job.
- [ ] Update README and Roadmap to mark Phase 8 complete only for validated 8A–8E behavior; retain Phase 9 physical hardware, browser, overlay visual, packaged full-flow, shutdown, and restart acceptance.
- [ ] Update architecture with the WindowsCollector, issue stripping, nullable flow, Overlay worker/message loop, frozen launcher, and package layout.
- [ ] Update data model with nullable Windows fields and state that no schema migration was required because existing columns accept NULL.
- [ ] Update testing strategy with the exact minimal 8A–8D checks, workflow static check, and all Phase 9 exclusions.
- [ ] Update CI/CD documentation with tag/manual behavior, permissions, artifact names, unsigned status, and the fact that manual dispatch cannot publish.
- [ ] Finalize the Phase 8 process note with the four commits, actual command evidence, tool versions/paths, package size/hash, workflow limitation, and remaining Phase 9 boundary.
- [ ] Run one static consistency group and no application suite:

```powershell
python -c "from pathlib import Path; p=Path('.github/workflows/release.yml').read_text(encoding='utf-8'); required=('workflow_dispatch','windows-latest','contents: write','gh release create','create_windows_release.ps1'); assert all(value in p for value in required)"
rg -n "Phase 8|WindowsCollector|ctypes|PyInstaller 6.22.2|SHA-256|unsigned|Phase 9" perfwatch\README.md perfwatch\docs
git diff --check
```

- [ ] Review the complete eight-file 8E diff, confirm no binary/secret/machine path is staged, then commit `ci: publish Windows releases`.
- [ ] Show the commit identifier and clean status. Record that `workflow_dispatch` and tag publication require the committed workflow to reach GitHub; do not claim a remote run that was not observed.

---

## Final Plan Self-Check

- [ ] Every design requirement maps to exactly one work item: collection/error honesty in 8A, Overlay in 8B, runtime in 8C, ZIP/checksum in 8D, and release/docs in 8E.
- [ ] 8A, 8C, and 8D use six stages; 8B uses three stages; 8E retains its approved exception.
- [ ] Mock selection is explicit in native wrapper, product launcher, package smoke, and documentation.
- [ ] Nullable names and signatures match from C++ optionals through Python `None`, SQLite NULL, TypeScript unions, Dashboard formatters, and Overlay model.
- [ ] No task adds a new endpoint, GUI framework, installer, service, updater, signer, Linux live collector, or GPU adapter.
- [ ] Test commands are scoped and not repeated across work items; Phase 9 owns physical and visual acceptance.
- [ ] Release version `0.1.0` is read from `python/pyproject.toml`; workflow tag validation prevents mismatched publication.
