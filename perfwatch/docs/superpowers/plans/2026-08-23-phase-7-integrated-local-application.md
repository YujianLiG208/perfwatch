# Phase 7 Integrated Local Application Implementation Plan

> **Required subskill:** Use `superpowers:subagent-driven-development` when the owner explicitly requests subagents; otherwise use `superpowers:executing-plans` and execute this plan in the current task, one approved stage at a time.

**Goal:** Deliver Roadmap Phase 7 as a deterministic evolving mock-data pipeline, analytics-enriched and SQLite-persisted estimates, a nullable-safe dashboard, and a single local server command that serves both the API/WebSocket endpoints and the production dashboard.

**Architecture:** Keep collection, analytics, persistence, API, and presentation as separate layers. Collectors produce raw snapshots; the service enriches a collected snapshot at the shared sampling boundary before storing it; SQLite persists the enriched projection with an idempotent legacy-schema migration; the dashboard consumes nullable API fields; a dedicated server entry point composes the existing FastAPI app with an optional static dashboard mount.

**Tech Stack:** C++17, pybind11, CMake/CTest, Python 3.12, FastAPI, Pydantic 2, SQLite, pytest, Ruff, React 19, TypeScript 6, Vite 8, Vitest, Testing Library.

**Spec:** [`docs/superpowers/specs/2026-08-23-phase-7-integrated-local-application-design.md`](../specs/2026-08-23-phase-7-integrated-local-application-design.md)

**Global Constraints:** Add no third-party dependencies; preserve every existing public endpoint and raw snapshot key; keep the native extension optional; make all new computed fields nullable; do not add installers, PyInstaller, system services, remote deployment, or Phase 8 work; stop before every stage transition; stop immediately before any command that requires a Ninja executable path.

## Mandatory execution protocol

Each work item (7A, 7B, 7C, 7D) uses the repository's exact six-stage pipeline. A stage must end with a report and an explicit wait for owner confirmation.

1. **Plan only:** confirm the applicable section of this document and list its exact file set. Do not edit implementation files.
2. **Implement visibly:** add tests first, observe the targeted red result, implement the smallest change, and run only targeted tests needed for the red/green loop. Do not run the broader validation suite.
3. **Validate only:** run the listed work-item validation commands. If a command would need a Ninja path, stop before invoking it and report the exact pending command.
4. **Update process note:** record implementation and validation evidence in the Phase 7 process note, then stop.
5. **Review Git diff:** inspect only the current work item's diff for scope, correctness, generated files, secrets, and accidental changes, then stop.
6. **Commit:** create the listed commit only after approval, verify the commit and clean worktree, then stop.

No stage may be combined with the next stage. An environment/tool failure ends the current attempt without retry, diagnosis, tool substitution, or PATH manipulation until the owner fixes the environment and explicitly resumes.

## File map

### Existing files to modify

- `cpp/include/perfwatch/collector.hpp` — indexed mock factory and stateful C++ collector.
- `cpp/src/collector.cpp` — deterministic triangle-wave mock values.
- `cpp/bindings/pybind_module.cpp` — optional `sample_index` Python binding.
- `cpp/tests/test_mock_collector.cpp` — C++ baseline, evolution, and repeatability tests.
- `python/src/perfwatch/collectors/mock.py` — indexed Python factory and stateful collector.
- `python/src/perfwatch/collectors/native.py` — indexed native/fallback calls and stateful wrapper.
- `python/src/perfwatch/api/service.py` — analytics enrichment at the sampling boundary.
- `python/src/perfwatch/api/app.py` — optional production dashboard mount after API/WebSocket routes.
- `python/src/perfwatch/storage/schema.sql` — nullable remaining-time column.
- `python/src/perfwatch/storage/sqlite_writer.py` — migration, insert, and metric reconstruction.
- `python/pyproject.toml` — `perfwatch-server` console command.
- `python/tests/test_mock_collector.py` — Python deterministic mock tests.
- `python/tests/test_service.py` — enrichment and analytics-error behavior.
- `python/tests/test_sqlite_writer.py` — schema migration and nullable round-trip.
- `python/tests/test_api.py` — enriched HTTP/WebSocket shape and static/API coexistence.
- `ui/dashboard/src/types.ts` — nullable battery estimate and process score.
- `ui/dashboard/src/data.ts` — remaining-time presentation helper.
- `ui/dashboard/src/App.tsx` — estimate rendering and nullable process summary.
- `ui/dashboard/src/components/ProcessTable.tsx` — nullable score rendering.
- `ui/dashboard/src/test/fixtures.ts` — enriched snapshot fixture.
- `ui/dashboard/src/App.test.tsx` — visible estimate and unavailable-score behavior.
- `ui/dashboard/src/data.test.ts` — duration formatting boundary tests.
- `README.md` — integrated local run instructions and Phase 7 status.
- `docs/roadmap.md` — mark Phase 7 complete without moving Phase 8 scope.
- `docs/architecture.md` — enrichment boundary and static-server composition.
- `docs/data_model.md` — new nullable field and migration behavior.
- `docs/testing_strategy.md` — Phase 7 test coverage and Ninja gate.

### New files to create

- `python/src/perfwatch/analytics/snapshot.py` — in-place snapshot enrichment coordinator.
- `python/tests/test_snapshot_enrichment.py` — pure enrichment unit tests.
- `python/src/perfwatch/server.py` — production local server CLI.
- `python/tests/test_server.py` — parser, dashboard validation, and `uvicorn.run` wiring tests.
- `ui/dashboard/.env.production` — same-origin production API/WebSocket roots.
- `docs/Phase 7 integrated local application.md` — process note populated only in each work item's process-note stage.

### Files intentionally unchanged

- `.github/workflows/ci.yml` — existing CI commands and toolchain remain authoritative.
- `python/src/perfwatch/analytics/battery_forecast.py` and `process_energy_score.py` — reuse existing formulas.
- `ui/dashboard/vite.config.ts` — retain development proxy behavior; production uses `.env.production`.
- Packaging/installers/system-service files — deferred to Roadmap Phase 8.

## Work item 7A — Deterministic evolving mock samples

**Outcome:** Every mock backend accepts an explicit non-negative sample index, returns the approved baseline at index 0, evolves deterministically through triangle waves, and keeps independent state in each collector instance.

**Commit:** `feat: add evolving mock samples`

### Stage 1 — Plan only

- [ ] Reconfirm that only the seven 7A files listed below are in scope:
  - `cpp/include/perfwatch/collector.hpp`
  - `cpp/src/collector.cpp`
  - `cpp/bindings/pybind_module.cpp`
  - `cpp/tests/test_mock_collector.cpp`
  - `python/src/perfwatch/collectors/mock.py`
  - `python/src/perfwatch/collectors/native.py`
  - `python/tests/test_mock_collector.py`
- [ ] Confirm there is no Ninja command in this stage.
- [ ] Stop and request approval for 7A Stage 2.

### Stage 2 — Implement visibly

#### Task 7A.1 — Add failing Python determinism tests

- [ ] Extend `python/tests/test_mock_collector.py` with exact baseline, evolution, repeatability, state, and invalid-index assertions:

```python
import pytest

from perfwatch.collectors.mock import MockCollector, get_mock_snapshot


def test_mock_snapshot_index_zero_preserves_baseline() -> None:
    snapshot = get_mock_snapshot(0)

    assert snapshot["timestamp_ms"] == 1_710_000_000_000
    assert snapshot["cpu"]["usage_percent"] == 42.5
    assert snapshot["memory"]["used_bytes"] == 17_179_869_184
    assert snapshot["battery"]["percent"] == 78.0
    assert snapshot["top_processes"][0]["estimated_power_score"] == 0.42


def test_mock_snapshot_is_deterministic_and_evolves() -> None:
    first = get_mock_snapshot(3)
    repeated = get_mock_snapshot(3)

    assert first == repeated
    assert first["timestamp_ms"] == 1_710_000_003_000
    assert first["cpu"]["usage_percent"] == 47.0
    assert first["battery"]["percent"] == 77.25
    assert first["top_processes"][0]["rss_bytes"] == 281_018_368


def test_mock_collector_advances_independently() -> None:
    first_collector = MockCollector()
    second_collector = MockCollector()

    assert first_collector.collect() == second_collector.collect()
    assert first_collector.collect()["timestamp_ms"] == 1_710_000_001_000
    assert second_collector.collect()["timestamp_ms"] == 1_710_000_001_000


def test_mock_snapshot_rejects_negative_index() -> None:
    with pytest.raises(ValueError, match="sample_index must be non-negative"):
        get_mock_snapshot(-1)
```

- [ ] Run only `python -m pytest python/tests/test_mock_collector.py -q` and confirm the new assertions fail because the current API is fixed and unindexed.

#### Task 7A.2 — Implement the Python indexed mock

- [ ] Change the public factory and collector in `python/src/perfwatch/collectors/mock.py` to use these exact helpers and formulas:

```python
def _triangle(sample_index: int, period: int) -> int:
    position = sample_index % period
    half_period = period // 2
    return position if position <= half_period else period - position


def get_mock_snapshot(sample_index: int = 0) -> dict[str, Any]:
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")

    triangle = _triangle(sample_index, 20)
    battery_triangle = _triangle(sample_index, 80)
    battery_position = sample_index % 80
    return {
        "timestamp_ms": 1_710_000_000_000 + sample_index * 1_000,
        "cpu": {
            "usage_percent": 42.5 + 1.5 * triangle,
            "frequency_mhz": 3_600.0 + 20.0 * triangle,
            "package_power_watts": 35.0 + 0.8 * triangle,
            "temperature_celsius": 65.0 + 0.4 * triangle,
        },
        "memory": {
            "total_bytes": 34_359_738_368,
            "used_bytes": 17_179_869_184 + 67_108_864 * triangle,
        },
        "battery": {
            "available": True,
            "charging": battery_position > 40,
            "percent": 78.0 - 0.25 * battery_triangle,
            "power_watts": 18.5 + 0.3 * triangle,
            "energy_remaining_wh": 45.0 - 0.2 * battery_triangle,
        },
        "gpu": {
            "available": False,
            "vendor": "unavailable",
            "usage_percent": 0.0,
            "vram_total_bytes": 0,
            "vram_used_bytes": 0,
            "power_watts": 0.0,
            "temperature_celsius": 0.0,
        },
        "top_processes": [
            {
                "pid": 1234,
                "name": "mock_process",
                "cpu_percent": 12.5 + 0.7 * triangle,
                "rss_bytes": 268_435_456 + 4_194_304 * triangle,
                "vram_bytes": 0,
                "estimated_power_score": 0.42 + 0.01 * triangle,
            }
        ],
    }


class MockCollector:
    def __init__(self) -> None:
        self._sample_index = 0

    def collect(self) -> dict[str, Any]:
        snapshot = get_mock_snapshot(self._sample_index)
        self._sample_index += 1
        return snapshot
```

- [ ] Run the targeted Python test again and confirm green.

#### Task 7A.3 — Add failing native-wrapper state tests

- [ ] Add tests to `python/tests/test_mock_collector.py` that monkeypatch a fake `perfwatch_native.get_mock_snapshot`, reload `perfwatch.collectors.native`, and assert calls receive `[0, 1]`; add the same assertion for the pure-Python fallback after removing the fake module.
- [ ] Use this exact call-recording contract in the fake module:

```python
calls: list[int] = []

def fake_get_mock_snapshot(sample_index: int = 0) -> dict[str, object]:
    calls.append(sample_index)
    return {"timestamp_ms": sample_index}
```

- [ ] Run only the new native-wrapper tests and confirm they fail because the current wrapper accepts no index and recreates state.

#### Task 7A.4 — Implement indexed native/fallback calls

- [ ] Update `python/src/perfwatch/collectors/native.py` to preserve an index per `NativeCollector` instance:

```python
def get_snapshot(sample_index: int = 0) -> dict[str, Any]:
    try:
        from perfwatch_native import get_mock_snapshot
    except ImportError:
        from perfwatch.collectors.mock import get_mock_snapshot

    return get_mock_snapshot(sample_index)


class NativeCollector:
    def __init__(self) -> None:
        self._sample_index = 0

    def collect(self) -> dict[str, Any]:
        snapshot = get_snapshot(self._sample_index)
        self._sample_index += 1
        return snapshot
```

- [ ] Run only the native-wrapper tests and confirm green.

#### Task 7A.5 — Add failing C++ evolution tests

- [ ] Replace equality-only assertions in `cpp/tests/test_mock_collector.cpp` with standard-library `assert` checks in the existing `main()` for `make_mock_snapshot(0)`, `make_mock_snapshot(3)`, repeatability at the same index, triangle reversal at index 11, and two independent `MockCollector` instances.
- [ ] Use exact numeric checks such as:

```cpp
const auto sample = perfwatch::make_mock_snapshot(3);
assert(sample.timestamp_ms == 1'710'000'003'000);
assert(sample.cpu.usage_percent == 47.0);
assert(sample.battery.percent == 77.25);
assert(sample.top_processes.at(0).rss_bytes == 281'018'368);

const auto peak = perfwatch::make_mock_snapshot(10);
const auto descending = perfwatch::make_mock_snapshot(11);
assert(peak.cpu.usage_percent > descending.cpu.usage_percent);
```

- [ ] **Ninja path gate:** stop immediately before the first CMake command that would require `-G Ninja` or `CMAKE_MAKE_PROGRAM` and request the owner-provided path.
- [ ] After the owner supplies/approves the path and explicitly resumes Stage 2, configure and build with that literal path, run `ctest --test-dir build-phase7 --output-on-failure -R perfwatch_cpp_tests`, and confirm the new evolution assertions fail against the fixed current implementation.

#### Task 7A.6 — Implement the C++ factory, collector state, and binding

- [ ] Update `cpp/include/perfwatch/collector.hpp` with `#include <cstdint>`, an indexed factory, and private state:

```cpp
class MockCollector final : public Collector {
public:
    SystemSnapshot collect() override;

private:
    std::uint64_t sample_index_{0};
};

SystemSnapshot make_mock_snapshot(std::uint64_t sample_index = 0);
```

- [ ] Implement the same integer triangle helpers and approved numeric formulas in `cpp/src/collector.cpp`; keep GPU unavailability and process identity unchanged:

```cpp
namespace {
std::uint64_t triangle(std::uint64_t sample_index, std::uint64_t period) {
    const auto position = sample_index % period;
    const auto half_period = period / 2;
    return position <= half_period ? position : period - position;
}
}  // namespace

SystemSnapshot MockCollector::collect() {
    const auto snapshot = make_mock_snapshot(sample_index_);
    ++sample_index_;
    return snapshot;
}

SystemSnapshot make_mock_snapshot(std::uint64_t sample_index) {
    const auto triangle_value = triangle(sample_index, 20);
    const auto battery_triangle = triangle(sample_index, 80);
    const auto wave = static_cast<double>(triangle_value);
    const auto battery_wave = static_cast<double>(battery_triangle);
    const auto battery_position = sample_index % 80;
    return SystemSnapshot{
        1'710'000'000'000LL + static_cast<std::int64_t>(sample_index * 1'000),
        CpuSample{
            42.5 + 1.5 * wave,
            3'600.0 + 20.0 * wave,
            35.0 + 0.8 * wave,
            65.0 + 0.4 * wave,
        },
        MemorySample{
            34'359'738'368ULL,
            17'179'869'184ULL + 67'108'864ULL * triangle_value,
        },
        BatterySample{
            true,
            battery_position > 40,
            78.0 - 0.25 * battery_wave,
            18.5 + 0.3 * wave,
            45.0 - 0.2 * battery_wave,
        },
        GpuSample{false, "unavailable", 0.0, 0ULL, 0ULL, 0.0, 0.0},
        std::vector<ProcessSample>{
            ProcessSample{
                1234,
                "mock_process",
                12.5 + 0.7 * wave,
                268'435'456ULL + 4'194'304ULL * triangle_value,
                0ULL,
                0.42 + 0.01 * wave,
            },
        },
    };
}
```

- [ ] Change `cpp/bindings/pybind_module.cpp` to bind the factory directly and retain the no-argument default:

```cpp
module.def(
    "get_mock_snapshot",
    [](std::uint64_t sample_index) {
        return snapshot_to_dict(perfwatch::make_mock_snapshot(sample_index));
    },
    pybind11::arg("sample_index") = 0
);
```

- [ ] Rebuild with the already approved literal Ninja path and run `ctest --test-dir build-phase7 --output-on-failure -R perfwatch_cpp_tests`; confirm the C++ mock tests are green.
- [ ] Run the already-green Python mock tests only if a Python-facing edit needs confirmation.
- [ ] Stop and request approval for 7A Stage 3.

### Stage 3 — Validate only

- [ ] Run `python -m pytest python/tests/test_mock_collector.py -q`.
- [ ] Run `python -m ruff check python/src/perfwatch/collectors python/tests/test_mock_collector.py`.
- [ ] **Ninja path gate:** stop before running these pending commands and report them verbatim with `<OWNER_NINJA_PATH>` unresolved:

```powershell
cmake -S cpp -B build-phase7 -G Ninja -DCMAKE_MAKE_PROGRAM="<OWNER_NINJA_PATH>" -Dpybind11_DIR="<VERIFIED_PYBIND11_CMAKE_DIR>"
cmake --build build-phase7
ctest --test-dir build-phase7 --output-on-failure
```

- [ ] After the owner provides/approves the Ninja path and explicitly resumes, run the three commands once. Any failure stops the stage.
- [ ] Stop and request approval for 7A Stage 4.

### Stages 4–6 — Process note, diff review, commit

- [ ] Stage 4: create `docs/Phase 7 integrated local application.md` with a `Phase 7A` section containing changed interfaces, targeted tests, broader validation results, the exact Ninja path used, and any remaining limitations; stop.
- [ ] Stage 5: inspect `git status --short`, `git diff --check`, and the 7A diff; verify no build directory or compiled extension is staged; stop.
- [ ] Stage 6: stage only the seven 7A implementation files, the process note, and this approved detailed implementation plan; commit `feat: add evolving mock samples`, show `git show --stat --oneline HEAD` and `git status --short`; stop.

## Work item 7B — Analytics enrichment, persistence, and dashboard display

**Outcome:** The shared sampling boundary computes nullable battery time remaining and process power scores, persists/reconstructs the battery estimate through SQLite, exposes both through HTTP/WebSocket responses, and renders them safely in the dashboard.

**Commit:** `feat: enrich and persist energy estimates`

### Stage 1 — Plan only

- [ ] Reconfirm the 7B file set from the file map and verify that the approved analytics formulas in `battery_forecast.py` and `process_energy_score.py` remain unchanged.
- [ ] Confirm no Ninja command is required by 7B.
- [ ] Stop and request approval for 7B Stage 2.

### Stage 2 — Implement visibly

#### Task 7B.1 — Specify pure enrichment behavior with failing tests

- [ ] Create `python/tests/test_snapshot_enrichment.py` with fresh dictionary fixtures for these cases:
  - available, discharging battery with numeric energy and power yields `energy / power * 3600`;
  - charging, unavailable, zero-power, missing, boolean, or non-numeric battery input yields `None`;
  - every process gets a recomputed score from CPU, RSS, and VRAM, replacing the raw mock score;
  - missing or invalid process inputs yield `None` without dropping the process;
  - the input dictionary object is returned and enriched in place.
- [ ] Use exact expected values:

```python
def test_enrich_snapshot_computes_battery_and_process_estimates() -> None:
    snapshot = {
        "battery": {
            "available": True,
            "charging": False,
            "energy_remaining_wh": 45.0,
            "power_watts": 18.5,
        },
        "top_processes": [
            {"cpu_percent": 12.5, "rss_bytes": 268_435_456, "vram_bytes": 0}
        ],
    }

    result = enrich_snapshot(snapshot)

    assert result is snapshot
    assert snapshot["battery"]["estimated_remaining_seconds"] == pytest.approx(
        8_756.756756756757
    )
    assert snapshot["top_processes"][0]["estimated_power_score"] == pytest.approx(0.1)
```

- [ ] Run only `python -m pytest python/tests/test_snapshot_enrichment.py -q` and confirm import/test failure because the coordinator does not exist.

#### Task 7B.2 — Implement the enrichment coordinator

- [ ] Create `python/src/perfwatch/analytics/snapshot.py` with strict validation and in-place enrichment:

```python
from collections.abc import MutableMapping
from math import isfinite
from typing import Any

from perfwatch.analytics.battery_forecast import estimate_remaining_seconds
from perfwatch.analytics.process_energy_score import estimate_process_power_score


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if isfinite(number) else None


def _non_negative_int(value: object) -> int | None:
    number = _number(value)
    if number is None or number < 0 or not number.is_integer():
        return None
    return int(number)


def enrich_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    battery = snapshot.get("battery")
    if isinstance(battery, MutableMapping):
        energy = _number(battery.get("energy_remaining_wh"))
        power = _number(battery.get("power_watts"))
        battery["estimated_remaining_seconds"] = (
            estimate_remaining_seconds(energy, power)
            if battery.get("available") is True
            and battery.get("charging") is False
            and energy is not None
            and energy >= 0
            and power is not None
            and power > 0
            else None
        )

    processes = snapshot.get("top_processes")
    if isinstance(processes, list):
        for process in processes:
            if not isinstance(process, MutableMapping):
                continue
            cpu = _number(process.get("cpu_percent"))
            rss = _non_negative_int(process.get("rss_bytes"))
            vram_value = process.get("vram_bytes", 0)
            vram = _non_negative_int(vram_value)
            process["estimated_power_score"] = (
                estimate_process_power_score(cpu, rss, vram)
                if cpu is not None and cpu >= 0 and rss is not None and vram is not None
                else None
            )

    return snapshot
```

- [ ] If the existing helper signatures reject the inferred static types, narrow locally without widening their public APIs.
- [ ] Run only `python -m pytest python/tests/test_snapshot_enrichment.py -q` and confirm green.

#### Task 7B.3 — Integrate enrichment into service sampling

- [ ] Add failing tests to `python/tests/test_service.py` asserting:
  - `sample_once()` sets the enriched snapshot as current and passes the same enriched value to `repository.add_snapshot`;
  - an enrichment exception records an event with `source == "analytics"`;
  - the raw collected snapshot still becomes current and is persisted after that exception.
- [ ] Monkeypatch the symbol used by `perfwatch.api.service` with an exact failure:

```python
def fail_enrichment(snapshot: dict[str, object]) -> dict[str, object]:
    raise RuntimeError("analytics failed")
```

- [ ] Run only the new service tests and confirm failure before implementation.
- [ ] In `python/src/perfwatch/api/service.py`, call enrichment after collection and before assigning/persisting, while isolating an unexpected analytics exception:

```python
snapshot = self.collector.collect()
try:
    enrich_snapshot(snapshot)
except Exception as error:
    self._record_error(source="analytics", error=error)

self.current_snapshot = snapshot
try:
    self.repository.add_snapshot(snapshot)
except Exception as error:
    self._record_error(source="storage", error=error)
```

- [ ] Retain the current collection-error behavior: a failed collection produces no current/persisted sample.
- [ ] Run the targeted service tests and confirm green.

#### Task 7B.4 — Persist the nullable battery estimate with an idempotent migration

- [ ] Add failing cases to `python/tests/test_sqlite_writer.py` for:
  - new databases contain `battery_estimated_remaining_seconds`;
  - initializing a legacy `samples_system` table adds the column and preserves an existing row;
  - a numeric estimate round-trips through `fetch_recent_metrics`;
  - a missing/`None` estimate round-trips as `None`.
- [ ] Build the legacy case from the exact Phase 6 schema by removing only the new column before initializing the writer:

```python
schema = (
    files("perfwatch.storage")
    .joinpath("schema.sql")
    .read_text(encoding="utf-8")
)
phase6_schema = schema.replace(
    "    battery_estimated_remaining_seconds REAL,\n",
    "",
)
with sqlite3.connect(database_path) as connection:
    connection.executescript(phase6_schema)
    connection.execute(
        "INSERT INTO samples_system (ts_ms) VALUES (?)",
        (1_709_999_999_000,),
    )
```

- [ ] Run only the new SQLite tests and confirm the absent-column/insert failures.
- [ ] Add `battery_estimated_remaining_seconds REAL` to `samples_system` in `python/src/perfwatch/storage/schema.sql`.
- [ ] In `SQLiteWriter.initialize`, execute the schema and then run an idempotent migration inside the same connection:

```python
columns = {
    row["name"]
    for row in connection.execute("PRAGMA table_info(samples_system)").fetchall()
}
if "battery_estimated_remaining_seconds" not in columns:
    connection.execute(
        "ALTER TABLE samples_system "
        "ADD COLUMN battery_estimated_remaining_seconds REAL"
    )
```

- [ ] Add the column to `SYSTEM_INSERT_SQL`, `_system_values`, and battery reconstruction in `_metric_from_row`; keep `None` unchanged when returned by `fetch_recent_metrics`.
- [ ] Count SQL columns and placeholders together in the test so the new insert has exactly 20 values.
- [ ] Run the targeted SQLite tests and confirm green.

#### Task 7B.5 — Lock the enriched API/WebSocket contract

- [ ] Extend `python/tests/test_api.py` to assert the first sampled response contains:

```python
assert payload["battery"]["estimated_remaining_seconds"] == pytest.approx(
    8_756.756756756757
)
assert payload["top_processes"][0]["estimated_power_score"] == pytest.approx(0.1)
```

- [ ] Assert the same two values in the latest `/metrics/recent`, `/processes/top`, and first `/ws/snapshot` payloads.
- [ ] Run only the new API cases; if they expose a serialization mismatch, fix it in the narrowest existing response-construction site and rerun only those cases.

#### Task 7B.6 — Make dashboard types and rendering nullable-safe

- [ ] Update `ui/dashboard/src/types.ts`:

```ts
export interface BatteryMetrics {
  available: boolean;
  charging: boolean;
  percent: number;
  power_watts: number;
  energy_remaining_wh: number;
  estimated_remaining_seconds: number | null;
}

export interface ProcessSample {
  timestamp_ms?: number;
  pid: number;
  name: string;
  cpu_percent: number;
  rss_bytes: number;
  vram_bytes: number;
  estimated_power_score: number | null;
}
```

- [ ] Add failing duration tests to `ui/dashboard/src/data.test.ts` for `null`, negative input, 59 seconds, 3,600 seconds, and 8,756.756 seconds.
- [ ] Add the minimal helper to `ui/dashboard/src/data.ts`:

```ts
export function formatDurationSeconds(value: number | null): string {
  if (value === null || !Number.isFinite(value) || value < 0) {
    return "Unavailable";
  }
  const totalMinutes = Math.round(value / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
}
```

- [ ] Update `ui/dashboard/src/test/fixtures.ts` with `estimated_remaining_seconds: 8756.756756756757` and retain the raw fixture process score only where a raw mock fixture is specifically needed; use `0.1` for enriched API fixtures.
- [ ] Add failing `ui/dashboard/src/App.test.tsx` assertions for `Estimated 2h 26m remaining` and `Unavailable` when a copied process has `estimated_power_score: null`.
- [ ] In `App.tsx`, render charging state first, then a discharging estimate, then unavailable state; guard process `.toFixed(3)` with `score != null`.
- [ ] In `ProcessTable.tsx`, render `score.toFixed(3)` only when non-null and render `Unavailable` otherwise.
- [ ] Run only `npm test -- --run src/data.test.ts src/App.test.tsx` from `ui/dashboard` and confirm green.
- [ ] Stop and request approval for 7B Stage 3.

### Stage 3 — Validate only

- [ ] Run `python -m pytest python/tests/test_snapshot_enrichment.py python/tests/test_service.py python/tests/test_sqlite_writer.py python/tests/test_api.py -q`.
- [ ] Run `python -m ruff check python/src/perfwatch/analytics/snapshot.py python/src/perfwatch/api/service.py python/src/perfwatch/storage python/tests/test_snapshot_enrichment.py python/tests/test_service.py python/tests/test_sqlite_writer.py python/tests/test_api.py`.
- [ ] From `ui/dashboard`, run `npm test -- --run`.
- [ ] From `ui/dashboard`, run `npm run build`.
- [ ] Stop and request approval for 7B Stage 4.

### Stages 4–6 — Process note, diff review, commit

- [ ] Stage 4: append a `Phase 7B` section to the process note with analytics fallbacks, schema migration evidence, API values, UI null handling, and validation output; stop.
- [ ] Stage 5: inspect `git diff --check`, verify SQL insert ordering against schema ordering, verify no dashboard `dist/` output is tracked, and inspect only the 7B diff; stop.
- [ ] Stage 6: stage only 7B files plus the process note, commit `feat: enrich and persist energy estimates`, show commit summary and clean status; stop.

## Work item 7C — Integrated local production server

**Outcome:** `perfwatch-server` validates a built dashboard directory, creates the existing FastAPI service, keeps API/WebSocket routes authoritative, and serves Vite production assets from the same origin.

**Commit:** `feat: serve integrated local dashboard`

### Stage 1 — Plan only

- [ ] Reconfirm this file set: `python/src/perfwatch/api/app.py`, `python/src/perfwatch/server.py`, `python/pyproject.toml`, `python/tests/test_api.py`, `python/tests/test_server.py`, and `ui/dashboard/.env.production`.
- [ ] Verify there is no new HTTP server, CLI, or static-serving dependency.
- [ ] Confirm no Ninja command is required by 7C.
- [ ] Stop and request approval for 7C Stage 2.

### Stage 2 — Implement visibly

#### Task 7C.1 — Configure same-origin production requests

- [ ] Create `ui/dashboard/.env.production` with exact values:

```dotenv
VITE_API_BASE_URL=/
VITE_WS_URL=/ws/snapshot
```

- [ ] Do not alter the Vite development proxy; development remains `npm run dev`, production remains a build served by FastAPI.

#### Task 7C.2 — Mount static assets after API/WebSocket routes

- [ ] Add failing tests to `python/tests/test_api.py` using `tmp_path` to create `index.html` and `assets/app.js`; assert `/`, `/assets/app.js`, `/health`, `/snapshot`, and `/ws/snapshot` all work from the same app.
- [ ] Extend `create_app` in `python/src/perfwatch/api/app.py` with an optional path:

```python
def create_app(
    settings: Settings | None = None,
    collector: Collector | None = None,
    repository: SnapshotRepository | None = None,
    dashboard_directory: Path | None = None,
) -> FastAPI:
```

- [ ] After every API router and WebSocket handler is registered, mount the dashboard last:

```python
if dashboard_directory is not None:
    app.mount(
        "/",
        StaticFiles(directory=dashboard_directory, html=True),
        name="dashboard",
    )
```

- [ ] Run only the new coexistence test and confirm green; specifically retain `/health` and `/ws/snapshot` behavior to prove mount order.

#### Task 7C.3 — Add and test the server entry point

- [ ] Create failing `python/tests/test_server.py` cases for:
  - default host `127.0.0.1` and port `8000`;
  - explicit `--host`, `--port`, and `--dashboard-directory`;
  - missing `index.html` exits through `ArgumentParser.error`;
  - valid arguments call `uvicorn.run` once with the composed app, host, and port.
- [ ] Implement `python/src/perfwatch/server.py` with import-safe parsing and a deterministic default build path:

```python
from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path

import uvicorn

from perfwatch.api.app import create_app


def default_dashboard_directory() -> Path:
    return Path(__file__).resolve().parents[3] / "ui" / "dashboard" / "dist"


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Run the PerfWatch local application")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--dashboard-directory",
        type=Path,
        default=default_dashboard_directory(),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)
    dashboard_directory = args.dashboard_directory.resolve()
    if not (dashboard_directory / "index.html").is_file():
        parser.error(
            f"dashboard build not found: {dashboard_directory / 'index.html'}"
        )
    app = create_app(dashboard_directory=dashboard_directory)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
```

- [ ] Add the script to `python/pyproject.toml` without changing the existing `perfwatch` command:

```toml
[project.scripts]
perfwatch = "perfwatch.cli:main"
perfwatch-server = "perfwatch.server:main"
```

- [ ] Run only `python -m pytest python/tests/test_server.py python/tests/test_api.py -q` and confirm green.
- [ ] Stop and request approval for 7C Stage 3.

### Stage 3 — Validate only

- [ ] From `ui/dashboard`, run `npm run build` and verify `dist/index.html` exists.
- [ ] Run `python -m pytest python/tests/test_server.py python/tests/test_api.py -q`.
- [ ] Run `python -m ruff check python/src/perfwatch/api/app.py python/src/perfwatch/server.py python/tests/test_api.py python/tests/test_server.py`.
- [ ] Run a non-blocking local smoke test through `TestClient`: `/`, `/health`, `/snapshot`, and `/ws/snapshot` must all respond; do not leave a server process running.
- [ ] Stop and request approval for 7C Stage 4.

### Stages 4–6 — Process note, diff review, commit

- [ ] Stage 4: append a `Phase 7C` section to the process note with CLI examples, mount-order reasoning, default path, production environment values, and smoke-test evidence; stop.
- [ ] Stage 5: inspect `git diff --check`; verify `dist/`, SQLite files, and runtime logs are untracked/ignored; verify static mounting occurs after every route; stop.
- [ ] Stage 6: stage only 7C files plus the process note, commit `feat: serve integrated local dashboard`, show commit summary and clean status; stop.

## Work item 7D — Documentation and full Phase 7 acceptance

**Outcome:** Project documentation accurately describes the completed integrated application, all non-Ninja suites pass, the owner-authorized Ninja path is used for the native acceptance suite, and no Phase 8 scope is claimed.

**Commit:** `docs: complete phase 7 integrated application`

### Stage 1 — Plan only

- [ ] Reconfirm the documentation-only file set: `README.md`, `docs/roadmap.md`, `docs/architecture.md`, `docs/data_model.md`, `docs/testing_strategy.md`, and the existing Phase 7 process note.
- [ ] Inventory the validation commands that already passed in 7A–7C and identify the owner-provided Ninja path without invoking it.
- [ ] Stop and request approval for 7D Stage 2.

### Stage 2 — Implement visibly

- [ ] Update `README.md` with a minimal local production flow:

```powershell
cd ui/dashboard
npm run build
cd ../..
python -m pip install -e python
perfwatch-server --host 127.0.0.1 --port 8000
```

- [ ] Document `--dashboard-directory` for non-default layouts and retain the existing development-mode commands.
- [ ] In `docs/roadmap.md`, mark Phase 7 complete with the four delivered work items while leaving packaging, installers, services, and distribution in Phase 8.
- [ ] In `docs/architecture.md`, describe this flow exactly: collector → enrichment → current snapshot → SQLite → HTTP/WebSocket → React, with static assets mounted last at `/`.
- [ ] In `docs/data_model.md`, document `battery.estimated_remaining_seconds: number | null`, recomputed `top_processes[].estimated_power_score: number | null`, the SQLite column, and the idempotent `PRAGMA table_info`/`ALTER TABLE` migration.
- [ ] In `docs/testing_strategy.md`, list the 7A–7C unit/integration coverage and state that native acceptance is gated on the explicit Ninja executable path.
- [ ] Normalize the process note headings and remove any provisional wording that contradicts completed evidence.
- [ ] Run only documentation link/path searches in this stage; do not run acceptance suites yet.
- [ ] Stop and request approval for 7D Stage 3.

### Stage 3 — Full acceptance validation

- [ ] Verify a clean dependency state without installing anything:

```powershell
python --version
node --version
npm --version
cmake --version
git --version
```

- [ ] Run the full Python suite and lint:

```powershell
python -m pytest python/tests -q
python -m ruff check python/src python/tests
```

- [ ] Run the full dashboard suite and production build:

```powershell
Set-Location ui/dashboard
npm test -- --run
npm run build
Set-Location ../..
```

- [ ] **Ninja path gate:** stop before the first native command, report the exact owner-provided path intended for `CMAKE_MAKE_PROGRAM`, and wait for explicit resume.
- [ ] After resume, run exactly once:

```powershell
cmake -S cpp -B build-phase7 -G Ninja -DCMAKE_MAKE_PROGRAM="<OWNER_NINJA_PATH>" -Dpybind11_DIR="<VERIFIED_PYBIND11_CMAKE_DIR>"
cmake --build build-phase7
ctest --test-dir build-phase7 --output-on-failure
```

- [ ] Run the native-backed Python mock test only after the extension path produced by the build is explicitly added for that command; do not permanently mutate PATH or the user environment.
- [ ] Perform the integrated `TestClient` smoke test for `/`, `/health`, `/snapshot`, `/metrics/recent`, `/processes/top`, and `/ws/snapshot`.
- [ ] Record exact command results in working notes, but do not edit the process note until Stage 4.
- [ ] Stop and request approval for 7D Stage 4.

### Stage 4 — Final process-note update

- [ ] Update the process note with the full acceptance command table, exit codes, test counts, the exact Ninja path and pybind11 CMake directory, integrated smoke results, and any limitations that remain true.
- [ ] State explicitly that packaging/distribution remains Phase 8.
- [ ] Stop and request approval for 7D Stage 5.

### Stage 5 — Final diff review

- [ ] Run `git status --short`, `git diff --check`, and inspect the entire uncommitted documentation/process-note diff.
- [ ] Search for stale states and forbidden placeholders:

```powershell
rg -n "awaiting written-spec review|T[B]D|T[O]DO|implement later|Phase 7.*planned" README.md docs
```

- [ ] Verify no `dist/`, `build-phase7/`, compiled extension, database, log, secret, or machine-specific absolute path is staged.
- [ ] Verify every Phase 7 claim has validation evidence and no Phase 8 feature is marked delivered.
- [ ] Stop and request approval for 7D Stage 6.

### Stage 6 — Documentation commit

- [ ] Stage only the six documentation files.
- [ ] Commit `docs: complete phase 7 integrated application`.
- [ ] Run `git show --stat --oneline HEAD` and `git status --short`.
- [ ] Stop and report Phase 7 completion only if the worktree is clean and every acceptance command above has fresh passing evidence.

## Plan self-review checklist

- [ ] Every approved Phase 7 requirement maps to at least one implementation task and one test or verification step.
- [ ] Python and C++ use identical sample-index semantics and formulas.
- [ ] The first mock sample preserves the approved Phase 6 baseline values.
- [ ] Battery estimates are present only for available, discharging, numerically valid samples.
- [ ] Process scores are recomputed at the shared sampling boundary and may be `None`.
- [ ] An analytics failure is observable but does not discard the raw sample.
- [ ] SQLite migration is additive, idempotent, and preserves existing rows.
- [ ] Static mounting cannot shadow API, health, or WebSocket routes.
- [ ] Production UI uses same-origin paths; development proxy remains unchanged.
- [ ] Each work item has all six mandatory stages and a stop after each.
- [ ] Every Ninja-dependent command is preceded by an explicit Ninja path stop gate.
- [ ] No task adds dependencies, packaging, installers, remote deployment, or Phase 8 behavior.
- [ ] The plan contains no unresolved implementation placeholder; angle-bracket values occur only in commands that must wait for owner-supplied verified tool paths.
