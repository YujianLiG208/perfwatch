# Phase 3–5 Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge the Phase 3 persistence branch and the Phase 4/5 service/dashboard branch into one validated `codex/phase-3-5-integration` history, then prepare it for a pull request to `main`.

**Architecture:** Keep the Phase 3 `SQLiteWriter` as the persistence foundation and add the Phase 4 service-facing query methods to it. Keep `SnapshotRepository` as a thin delegation layer so the service, API, and tests use one storage implementation without adapters or duplicated queries.

**Tech Stack:** Git, Python 3.11/3.12, SQLite, FastAPI, pytest, Ruff, C++17, CMake/CTest, Node.js 22, React/Vite/Vitest.

## Global Constraints

- Do not rewrite `codex/phase-3-sqlite-persistence`, `codex/phase-4-service-loop`, or `codex/phase-5`.
- The target history must contain commits `8298574`, `27db3f6`, and `780dd05`.
- Execute this plan only on `codex/phase-3-5-integration`; do not add integration commits to another branch.
- Do not stage or overwrite pre-existing user changes to `perfwatch/README.md` or `perfwatch/AGENTS.md`.
- Stop before Task 1 if the dedicated execution worktree is not clean; ask the owner to commit or relocate pre-existing changes. Do not stash them automatically.
- Open this plan from the Codex task/worktree already assigned to `codex/phase-3-5-integration`; do not switch branches while executing it.
- Use `superpowers:using-git-worktrees` before execution to verify that the task is isolated; if it is not isolated, stop and create a dedicated Codex worktree for `codex/phase-3-5-integration` before continuing.
- Preserve Python 3.11+, C++17, deterministic mock tests, and fixture-only hardware parser tests.
- Do not add Terraform, cloud infrastructure, remote telemetry, storage adapters, or new persistence dependencies.
- Follow the repository stage order for every task: Plan only, Implement visibly, Validate only, update the applicable process note, review the scoped diff, commit.
- Run Git commands from the Git repository root. Run Python, CMake, npm, and Ruff commands from the nested `perfwatch/` project root.

---

## File Map

### Merge-resolved implementation files

- `perfwatch/python/src/perfwatch/storage/sqlite_writer.py`: one SQLite implementation containing Phase 3 writes/query windows/retention and Phase 4 dashboard queries.
- `perfwatch/python/src/perfwatch/storage/repository.py`: thin public interface consumed by `ServiceState` and API routes.
- `perfwatch/python/tests/test_sqlite_writer.py`: combined Phase 3 and Phase 4 persistence behavior, including rollback coverage.

### Merge-resolved documentation

- `perfwatch/docs/roadmap.md`: mark Phase 3–5 as integrated while preserving Phase 6–9.
- `perfwatch/docs/testing_strategy.md`: describe persistence, service, frontend, mock, fixture, and hardware limitations together.

### Automatically merged Phase 3 files to verify

- `perfwatch/python/src/perfwatch/storage/schema.sql`: timestamp indexes for system, process, and event tables.
- `perfwatch/docs/data_model.md`: Phase 3 data-model documentation.

### Phase 5 callers that must remain unchanged unless a failing test proves otherwise

- `perfwatch/python/src/perfwatch/api/service.py`
- `perfwatch/python/src/perfwatch/api/routes.py`
- `perfwatch/python/src/perfwatch/api/app.py`
- `perfwatch/python/tests/test_api.py`
- `perfwatch/python/tests/test_service.py`
- `perfwatch/ui/dashboard/`

---

### Task 0: Verify the `codex/phase-3-5-integration` Execution Worktree

**Files:**

- No repository file changes.

**Interfaces:**

- Consumes: a new Codex task/worktree already assigned to `codex/phase-3-5-integration`, based on commit `f192370` or a descendant containing the approved designs and implementation plans.
- Produces: a clean, isolated `codex/phase-3-5-integration` worktree ready for the Phase merges.

- [ ] **Step 1: Invoke the required worktree skill**

Use `superpowers:using-git-worktrees` to verify that the current Codex task is already isolated. Do not create or switch branches, and do not continue in the original working copy. If the skill reports that the task is not isolated, stop and create a dedicated Codex worktree for the existing `codex/phase-3-5-integration` branch.

- [ ] **Step 2: Verify the dedicated integration worktree**

Run from the Git repository root in that worktree:

```powershell
git branch --show-current
git status --short
git merge-base --is-ancestor f192370 HEAD
```

Expected: branch is exactly `codex/phase-3-5-integration`, status is empty, and the ancestry command exits 0. If README or `AGENTS.md` is modified/untracked, stop and ask the owner to commit or relocate it; do not stash or delete it.

---

### Task 1: Establish the Phase 5 Integration Baseline

**Files:**

- Merge from: `codex/phase-5`
- Verify: `perfwatch/python/tests/`
- Verify: `perfwatch/cpp/tests/`
- Verify: `perfwatch/ui/dashboard/`

**Interfaces:**

- Consumes: `codex/phase-3-5-integration` containing the approved design documents and implementation plans.
- Produces: `codex/phase-3-5-integration` history containing `27db3f6` and `780dd05`, with Phase 5 tests passing before Phase 3 is introduced.

- [ ] **Step 1: Verify the execution preconditions**

Run:

```powershell
git branch --show-current
git status --short
git merge-base --is-ancestor 27db3f6 codex/phase-5
git merge-base --is-ancestor 780dd05 codex/phase-5
```

Expected: the isolated worktree is on `codex/phase-3-5-integration`, `git status --short` is empty, and both ancestry commands exit 0.

- [ ] **Step 2: Merge the published Phase 5 history**

Run:

```powershell
git merge --no-edit codex/phase-5
```

Expected: a merge commit is created because `codex/phase-3-5-integration` already contains the approved design and plan commits; no published Phase branch is rewritten.

- [ ] **Step 3: Install the merged development dependencies**

Run from `perfwatch/`:

```powershell
python -m pip install -e "python[dev]" pybind11
npm --prefix ui/dashboard ci
```

Expected: both commands exit 0.

- [ ] **Step 4: Verify the Phase 5 Python and frontend baseline**

Run:

```powershell
python -m pytest python/tests
npm --prefix ui/dashboard test
npm --prefix ui/dashboard run build
```

Expected: pytest, Vitest, TypeScript, and Vite all pass. If this baseline fails, stop and diagnose the Phase 5 failure before merging Phase 3.

- [ ] **Step 5: Verify the Phase 5 native baseline**

Run:

```powershell
cmake -S cpp -B build
cmake --build build --config Release
ctest --test-dir build --output-on-failure -C Release
```

Expected: CMake configure/build and all CTest cases pass.

- [ ] **Step 6: Record the baseline commit**

Run:

```powershell
git log -1 --oneline
git status --short
```

Expected: HEAD is the Phase 5 merge commit and the worktree is clean. The merge command in Step 2 is the task commit; do not create an empty follow-up commit.

---

### Task 2: Merge Phase 3 and Resolve the Persistence Boundary

**Files:**

- Modify: `perfwatch/python/src/perfwatch/storage/sqlite_writer.py`
- Modify: `perfwatch/python/src/perfwatch/storage/repository.py`
- Modify: `perfwatch/python/tests/test_sqlite_writer.py`
- Resolve minimally: `perfwatch/docs/roadmap.md`
- Resolve minimally: `perfwatch/docs/testing_strategy.md`
- Verify: `perfwatch/python/src/perfwatch/storage/schema.sql`
- Verify: `perfwatch/docs/data_model.md`

**Interfaces:**

- Consumes: Phase 3 `SQLiteWriter.insert_snapshots()`, time-window queries, event writes, and retention cleanup; Phase 5 `ServiceState` repository calls.
- Produces: one `SQLiteWriter` supporting both Phase 3 and Phase 5 behavior and one `SnapshotRepository` exposing the exact methods below.

Final repository methods:

```python
initialize() -> None
add_snapshot(snapshot: dict[str, Any]) -> int
add_snapshots(snapshots: Iterable[Mapping[str, Any]]) -> list[int]
add_process_samples(timestamp_ms: int, processes: Iterable[Mapping[str, Any]]) -> int
add_event(*, timestamp_ms: int, level: str, source: str, message: str) -> int
recent_system_samples(since_timestamp_ms: int, until_timestamp_ms: int | None = None, limit: int | None = None) -> list[dict[str, Any]]
recent_process_samples(since_timestamp_ms: int, until_timestamp_ms: int | None = None, limit: int | None = None) -> list[dict[str, Any]]
get_recent_metrics(*, limit: int = 100) -> list[dict[str, Any]]
get_top_processes(*, limit: int = 10, timestamp_ms: int | None = None) -> list[dict[str, Any]]
apply_retention_policy(older_than_timestamp_ms: int) -> dict[str, int]
close() -> None
```

- [ ] **Step 1: Start the Phase 3 merge without committing**

Run:

```powershell
git merge --no-commit codex/phase-3-sqlite-persistence
git diff --name-only --diff-filter=U
```

Expected: Git stops for conflicts. The unresolved list is limited to the audited overlap: roadmap, testing strategy, repository, writer, and writer tests.

- [ ] **Step 2: Use Phase 3 as the starting point for the three persistence conflicts**

Run:

```powershell
git checkout --theirs -- perfwatch/python/src/perfwatch/storage/sqlite_writer.py
git checkout --theirs -- perfwatch/python/src/perfwatch/storage/repository.py
git checkout --theirs -- perfwatch/python/tests/test_sqlite_writer.py
git checkout --ours -- perfwatch/docs/roadmap.md
git checkout --ours -- perfwatch/docs/testing_strategy.md
```

Expected: the implementation/test files contain Phase 3 behavior; documentation remains temporarily at Phase 5 wording for a focused follow-up task.

- [ ] **Step 3: Run the Phase 4/5 tests to prove the Phase 3-only interface is insufficient**

Run:

```powershell
python -m pytest python/tests/test_api.py python/tests/test_service.py -v
```

Expected: FAIL because the Phase 3 repository lacks `initialize`, `get_recent_metrics`, `get_top_processes`, or `close`.

- [ ] **Step 4: Add a rollback regression test before changing the writer**

Add to `perfwatch/python/tests/test_sqlite_writer.py`:

```python
import pytest


def test_sqlite_writer_rolls_back_snapshot_batch_on_invalid_process(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)
    valid = snapshot_at(1000, "valid")
    invalid = snapshot_at(2000, "invalid")
    invalid["top_processes"][0]["rss_bytes"] = "not-an-integer"

    with pytest.raises(ValueError):
        writer.insert_snapshots([valid, invalid])

    with sqlite3.connect(database_path) as connection:
        system_count = connection.execute("SELECT COUNT(*) FROM samples_system").fetchone()[0]
        process_count = connection.execute("SELECT COUNT(*) FROM samples_process").fetchone()[0]

    assert system_count == 0
    assert process_count == 0
```

- [ ] **Step 5: Run the rollback test to establish its result against Phase 3**

Run:

```powershell
python -m pytest python/tests/test_sqlite_writer.py::test_sqlite_writer_rolls_back_snapshot_batch_on_invalid_process -v
```

Expected: PASS. This test records the Phase 3 transaction guarantee so later query additions cannot regress it.

- [ ] **Step 6: Add the Phase 5 dashboard query test**

Add to `perfwatch/python/tests/test_sqlite_writer.py`:

```python
def test_sqlite_writer_fetches_dashboard_metrics_and_top_processes(tmp_path) -> None:
    database_path = tmp_path / "perfwatch.sqlite3"
    writer = SQLiteWriter(database_path)
    writer.insert_snapshots(
        [
            snapshot_at(1000, "old"),
            snapshot_at(2000, "latest"),
        ]
    )

    metrics = writer.fetch_recent_metrics(limit=1)
    processes = writer.fetch_top_processes(limit=1)

    assert [metric["timestamp_ms"] for metric in metrics] == [2000]
    assert metrics[0]["cpu"]["usage_percent"] == 42.5
    assert [process["name"] for process in processes] == ["latest"]
```

- [ ] **Step 7: Run the dashboard query test to verify it fails**

Run:

```powershell
python -m pytest python/tests/test_sqlite_writer.py::test_sqlite_writer_fetches_dashboard_metrics_and_top_processes -v
```

Expected: FAIL with missing `fetch_recent_metrics` or `fetch_top_processes`.

- [ ] **Step 8: Add the Phase 5 query methods to the Phase 3 writer**

Add `fetch_recent_metrics`, `fetch_top_processes`, `close`, and `_metric_from_row` to `SQLiteWriter`. Copy their SQL and row-shaping behavior from commit `780dd05` without changing the Phase 3 insertion/query/retention methods. The required public behavior is:

```python
def fetch_recent_metrics(self, *, limit: int = 100) -> list[dict[str, Any]]:
    self.initialize()
    with closing(self.connect()) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM samples_system
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [self._metric_from_row(row) for row in rows]

def fetch_top_processes(
    self,
    *,
    limit: int = 10,
    timestamp_ms: int | None = None,
) -> list[dict[str, Any]]:
    self.initialize()
    with closing(self.connect()) as connection:
        if timestamp_ms is None:
            latest = connection.execute(
                "SELECT ts_ms FROM samples_system ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if latest is None:
                return []
            timestamp_ms = int(latest["ts_ms"])

        rows = connection.execute(
            """
            SELECT
                process.ts_ms,
                process.pid,
                process.name,
                process.cpu_percent,
                process.rss_bytes,
                process.vram_bytes,
                process.estimated_power_score
            FROM samples_process AS process
            INNER JOIN (
                SELECT pid, MAX(id) AS id
                FROM samples_process
                WHERE ts_ms = ?
                GROUP BY pid
            ) AS latest_process ON latest_process.id = process.id
            ORDER BY
                process.estimated_power_score DESC,
                process.cpu_percent DESC,
                process.id DESC
            LIMIT ?
            """,
            (timestamp_ms, limit),
        ).fetchall()
    return [_row_to_public_dict(row) for row in rows]

def close(self) -> None:
    return None

@staticmethod
def _metric_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "timestamp_ms": row["ts_ms"],
        "cpu": {
            "usage_percent": row["cpu_usage_percent"],
            "frequency_mhz": row["cpu_frequency_mhz"],
            "package_power_watts": row["cpu_package_power_watts"],
            "temperature_celsius": row["cpu_temperature_celsius"],
        },
        "memory": {
            "total_bytes": row["memory_total_bytes"],
            "used_bytes": row["memory_used_bytes"],
        },
        "battery": {
            "available": bool(row["battery_available"]),
            "charging": bool(row["battery_charging"]),
            "percent": row["battery_percent"],
            "power_watts": row["battery_power_watts"],
            "energy_remaining_wh": row["battery_energy_remaining_wh"],
        },
        "gpu": {
            "available": bool(row["gpu_available"]),
            "vendor": row["gpu_vendor"],
            "usage_percent": row["gpu_usage_percent"],
            "vram_total_bytes": row["gpu_vram_total_bytes"],
            "vram_used_bytes": row["gpu_vram_used_bytes"],
            "power_watts": row["gpu_power_watts"],
            "temperature_celsius": row["gpu_temperature_celsius"],
        },
    }
```

Keep this nested response shape exactly. Do not return database `id` fields.

- [ ] **Step 9: Expand the Phase 3 repository with the Phase 5 service interface**

Add these exact methods to `SnapshotRepository`; keep the existing Phase 3 methods unchanged:

```python
def initialize(self) -> None:
    self.writer.initialize()

def get_recent_metrics(self, *, limit: int = 100) -> list[dict[str, Any]]:
    return self.writer.fetch_recent_metrics(limit=limit)

def get_top_processes(
    self,
    *,
    limit: int = 10,
    timestamp_ms: int | None = None,
) -> list[dict[str, Any]]:
    return self.writer.fetch_top_processes(limit=limit, timestamp_ms=timestamp_ms)

def close(self) -> None:
    self.writer.close()
```

Change `add_event` to the Phase 5 keyword-only signature and delegate with keyword arguments:

```python
def add_event(
    self,
    *,
    timestamp_ms: int,
    level: str,
    source: str,
    message: str,
) -> int:
    return self.writer.insert_event(
        timestamp_ms=timestamp_ms,
        level=level,
        source=source,
        message=message,
    )
```

- [ ] **Step 10: Run the combined persistence, service, and API tests**

Run:

```powershell
python -m pytest python/tests/test_sqlite_writer.py python/tests/test_service.py python/tests/test_api.py -v
```

Expected: PASS, including rollback, retention, dashboard history, top-process queries, service sampling, and WebSocket/API behavior.

- [ ] **Step 11: Resolve and stage the merge**

Run:

```powershell
git add perfwatch/python/src/perfwatch/storage/sqlite_writer.py
git add perfwatch/python/src/perfwatch/storage/repository.py
git add perfwatch/python/tests/test_sqlite_writer.py
git add perfwatch/docs/roadmap.md perfwatch/docs/testing_strategy.md
git add perfwatch/python/src/perfwatch/storage/schema.sql perfwatch/docs/data_model.md
git diff --name-only --diff-filter=U
git diff --cached --check
```

Expected: no unresolved paths and no whitespace errors.

- [ ] **Step 12: Review and commit the semantic merge**

Run:

```powershell
git diff --cached --stat
git diff --cached
git commit -m "merge: integrate phase 3 persistence with phase 5"
```

Expected: one merge commit with both parents and the reviewed persistence resolution.

---

### Task 3: Reconcile Project Documentation and Run the Full Integration Gate

**Files:**

- Modify: `perfwatch/README.md`
- Modify: `perfwatch/docs/architecture.md`
- Modify: `perfwatch/docs/data_model.md`
- Modify: `perfwatch/docs/roadmap.md`
- Modify: `perfwatch/docs/testing_strategy.md`

**Interfaces:**

- Consumes: the merged persistence/service/dashboard behavior from Task 2.
- Produces: accurate project documentation and a fully validated integration commit ready for CI/CD implementation.

- [ ] **Step 1: Update the integrated status text**

Use these exact facts throughout the five documents:

```text
- Phase 3 persistence, Phase 4 service loop, and Phase 5 dashboard are integrated on codex/phase-3-5-integration.
- main remains the Phase 2 baseline until the integration pull request is merged.
- Linux support is fixture/parser-only; live Linux, Windows PDH/WMI, GPU, overlay, and installers remain incomplete.
- Automated tests use deterministic mocks and fixtures and do not validate physical sensors.
- SQLite supports single and batch snapshot writes, events, history queries, top-process queries, indexes, and retention cleanup.
```

Do not copy the pre-existing uncommitted README from another worktree without owner confirmation.

- [ ] **Step 2: Run the complete Python quality and test gate**

Run from `perfwatch/`:

```powershell
python -m ruff check python/src python/tests
python -m pytest python/tests
```

Expected: both commands pass with zero errors and zero failed tests.

- [ ] **Step 3: Run the complete native gate**

Run:

```powershell
cmake -S cpp -B build
cmake --build build --config Release
ctest --test-dir build --output-on-failure -C Release
```

Expected: configure/build pass and CTest reports zero failures.

- [ ] **Step 4: Run the complete frontend gate**

Run:

```powershell
npm --prefix ui/dashboard ci
npm --prefix ui/dashboard test
npm --prefix ui/dashboard run build
```

Expected: locked installation, Vitest, TypeScript, and Vite all pass.

- [ ] **Step 5: Verify ancestry and repository honesty**

Run:

```powershell
git merge-base --is-ancestor 8298574 HEAD
git merge-base --is-ancestor 27db3f6 HEAD
git merge-base --is-ancestor 780dd05 HEAD
rg -n "<<<<<<<|=======|>>>>>>>" perfwatch/python perfwatch/cpp perfwatch/ui perfwatch/docs --glob "!superpowers/plans/**"
git status --short
```

Expected: all ancestry commands exit 0, ripgrep finds no conflict markers, and only the five scoped documentation files are modified.

- [ ] **Step 6: Review and commit the documentation reconciliation**

Run:

```powershell
git add perfwatch/README.md perfwatch/docs/architecture.md perfwatch/docs/data_model.md perfwatch/docs/roadmap.md perfwatch/docs/testing_strategy.md
git diff --cached --check
git diff --cached
git commit -m "docs: describe integrated phase 3 through 5 baseline"
```

Expected: one documentation-only commit.

- [ ] **Step 7: Record the final integration evidence**

Run:

```powershell
git log --graph --decorate --oneline -12
git status --short
```

Expected: the graph visibly contains both Phase branches, the documentation commit is HEAD, and the worktree is clean.

---

### Task 4: Publish the Integration Pull Request and Verify `main`

**Files:**

- No repository file changes.

**Interfaces:**

- Consumes: clean, fully validated `codex/phase-3-5-integration` integration history.
- Produces: owner-approved `main` history containing the Phase 3, Phase 4, and Phase 5 commits.

- [ ] **Step 1: Verify GitHub authentication and push the integration branch**

Run from the Git repository root:

```powershell
gh auth status
git push origin codex/phase-3-5-integration
```

Expected: authentication succeeds and the remote integration branch matches local HEAD. If authentication is invalid, stop and ask the owner to reauthenticate; do not replace credentials automatically.

- [ ] **Step 2: Open the integration-only pull request**

Run:

```powershell
gh pr create --base main --head codex/phase-3-5-integration --title "Integrate Phase 3 through 5" --body "Combines Phase 3 SQLite persistence with the Phase 4 service loop and Phase 5 dashboard. Full Python, C++, frontend, and Ruff validation completed locally."
```

If the pull request already exists, use `gh pr view --web` instead of creating a duplicate.

Expected: the pull request contains integration and documentation commits only; CI/CD implementation is absent.

- [ ] **Step 3: Wait for owner review and merge**

Do not merge automatically. Provide the merge graph, validation output, and conflict-resolution summary to the owner, then wait for explicit approval and repository merge.

- [ ] **Step 4: Verify the merged remote baseline**

After the owner merges the pull request, run:

```powershell
git fetch origin main
git merge-base --is-ancestor 8298574 origin/main
git merge-base --is-ancestor 27db3f6 origin/main
git merge-base --is-ancestor 780dd05 origin/main
```

Expected: all three ancestry commands exit 0.

---

## Plan Completion Gate

Do not begin the CI/CD implementation plan until all of the following are true:

- The three Phase commits are ancestors of `codex/phase-3-5-integration`.
- Full Python, C++, and frontend validation has fresh passing output.
- The integrated documentation states the remaining hardware limitations accurately.
- The working tree is clean.
- The complete integration diff and merge graph have been reviewed.
- The owner has merged the integration pull request and `origin/main` contains all three Phase commits.

## Plan Review Record

- Reviewed against `Phase 3-5 audit and integration.md` on 2026-08-03.
- Verified coverage for published-branch ancestry, the five audited conflicts, Phase 3 transaction/query/retention behavior, Phase 4 service interfaces, Phase 5 frontend validation, and owner-approved merge to `main`.
- Verified that writer and repository method names/signatures match their service and test consumers.
- Corrected the execution context on 2026-08-19 so setup, integration, documentation, push, pull request, and completion steps all target `codex/phase-3-5-integration`.
- Revalidation passed 11 branch-plan assertions, the placeholder scan, and `git diff --check`.
- Placeholder and trailing-whitespace scans passed.
- No merge or implementation test was run while writing this plan; all executable validation commands are assigned to implementation tasks above.
