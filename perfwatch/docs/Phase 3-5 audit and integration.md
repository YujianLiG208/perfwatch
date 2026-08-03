# Phase 3–5 Audit and Integration

**Status:** Approved design

**Date:** 2026-08-03

**Target branch:** `codex/cicd`, followed by a pull request to `main`

## Purpose

Unify the completed Phase 3, Phase 4, and Phase 5 work without rewriting their published branch
history. The integrated branch must retain Phase 3 persistence hardening, the Phase 4 service loop,
and the Phase 5 dashboard as one testable baseline for CI/CD work.

## Audited Branch State

| Branch | Commit | Relationship and scope |
| --- | --- | --- |
| `main` | `ac992ae` | Phase 2 Linux fixture parsers; common base for later phases. |
| `codex/cicd` | `ac992ae` | Current integration target; no integration commits yet. |
| `codex/phase-3-sqlite-persistence` | `8298574` | Phase 3 persistence work, based directly on Phase 2. |
| `codex/phase-4-service-loop` | `27db3f6` | Phase 4 service work, also based directly on Phase 2. |
| `codex/phase-5` | `780dd05` | Phase 5 dashboard work; includes Phase 4 in its ancestry. |

The current topology is effectively:

```text
Phase 2 (main)
├── Phase 3 persistence
└── Phase 4 service loop ── Phase 5 dashboard
```

Phase 3 is therefore not an ancestor of Phase 4 or Phase 5. A Phase 5-only merge would omit the
dedicated Phase 3 persistence behavior.

## Implemented Scope to Preserve

### Phase 3

- Hardened SQLite writes and transaction behavior.
- Batch insertion of system and process samples.
- Event persistence.
- Recent-sample queries.
- Supporting indexes.
- Retention cleanup.
- Expanded persistence tests and data-model documentation.

### Phase 4

- Background sampling service.
- SQLite-backed API queries.
- Recent metrics and top-process endpoints.
- WebSocket snapshot streaming.
- Runtime settings and graceful shutdown.

### Phase 5

- Vite, React, and TypeScript dashboard.
- Current metrics, history charts, and process views.
- WebSocket updates with HTTP fallback.
- Frontend unit tests and production build command.

## Integration Options Considered

### Merge published histories — selected

Advance `codex/cicd` to Phase 5, then merge Phase 3 and resolve the shared persistence files
semantically. This preserves both published histories and leaves a visible merge relationship.

### Rebuild a linear history

Cherry-pick or rebase Phase 4 and Phase 5 onto Phase 3. This produces a linear history but rewrites
published work and still requires semantic conflict resolution.

### Port Phase 3 manually onto Phase 5

Reimplement selected persistence behavior on top of Phase 5. This can produce a small final diff,
but it loses ancestry and creates the highest risk of silently omitting Phase 3 behavior.

## Selected Integration Procedure

1. Preserve the existing modified `README.md` and untracked `AGENTS.md`; do not stage or overwrite
   them as part of integration.
2. Perform integration in an isolated worktree or an otherwise clean checkout of `codex/cicd`.
3. Merge `codex/phase-5` into `codex/cicd`. Because both currently descend from `ac992ae`, this
   should advance the integration baseline to Phase 5 without rewriting Phase 5.
4. Merge `codex/phase-3-sqlite-persistence` into the resulting branch.
5. Resolve the shared files according to the rules below.
6. Run the complete Python, C++, frontend, and quality validation set.
7. Review the full diff and merge result before committing the conflict resolution.
8. Open a pull request from `codex/cicd` to `main` only after all acceptance criteria pass.

The existing Phase 3, Phase 4, and Phase 5 branches remain unchanged.

## Shared Files and Resolution Rules

The audit found five paths changed by both Phase 3 and Phase 5:

| Path | Resolution rule |
| --- | --- |
| `docs/roadmap.md` | Describe Phase 3–5 as integrated work and preserve later roadmap phases. |
| `docs/testing_strategy.md` | Combine persistence, service, and dashboard validation; do not claim real-hardware coverage. |
| `python/src/perfwatch/storage/repository.py` | Preserve the repository interface required by the Phase 4 service while retaining Phase 3 query and cleanup behavior. |
| `python/src/perfwatch/storage/sqlite_writer.py` | Preserve Phase 4 call compatibility and restore Phase 3 transaction, batching, event, index, and retention guarantees. |
| `python/tests/test_sqlite_writer.py` | Retain both Phase 3 persistence cases and Phase 4 service-facing expectations, adapting assertions only where the integrated API requires it. |

`docs/data_model.md` and `python/src/perfwatch/storage/schema.sql` are Phase 3-owned changes and
should enter the integration unchanged unless validation exposes a real incompatibility.

## Semantic Merge Requirements

Textual conflict resolution is insufficient for the persistence layer. The integrated result must
demonstrate all of the following:

- The service can start with a newly created database.
- Existing Phase 4 API queries use the integrated repository without adapter duplication.
- A batch write is atomic: partial system/process data is not committed on failure.
- Event writes and recent-sample queries remain available.
- Retention cleanup removes expired related rows without violating database integrity.
- Required indexes are created for the history and process-query paths.
- The mock collector remains the default validation path; no test requires real hardware.

## Validation Commands

Run from the `perfwatch` project root:

```powershell
python -m pytest python/tests
python -m ruff check python/src python/tests
cmake -S cpp -B build
cmake --build build --config Release
ctest --test-dir build --output-on-failure -C Release
npm --prefix ui/dashboard ci
npm --prefix ui/dashboard test
npm --prefix ui/dashboard run build
```

Windows and Linux CI must execute the native/Python validation. Frontend validation may run once on
Linux because it has no platform-specific runtime integration in Phase 5.

## Acceptance Criteria

- `codex/cicd` contains commits `8298574`, `27db3f6`, and `780dd05` in its ancestry.
- No merge markers or unresolved paths remain.
- Phase 3 persistence tests, Phase 4 service/API tests, Phase 5 frontend tests, and C++ tests pass.
- Ruff reports no errors in Python source or tests.
- The dashboard production build succeeds.
- No validation depends on live `/proc`, `/sys`, PDH, WMI, GPU, or battery hardware.
- The complete integration diff has been reviewed before the pull request is opened.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Phase 3 and Phase 4 evolved different storage interfaces. | Resolve at the repository/writer boundary and exercise both storage and service tests. |
| A conflict resolution keeps method names but loses transaction guarantees. | Retain explicit Phase 3 atomicity and rollback tests. |
| Database schema and query code drift apart. | Validate creation of a fresh database and every repository query used by the service. |
| Documentation overstates hardware support. | Keep deterministic mock and fixture limitations explicit. |
| Current working-tree changes are accidentally included. | Use an isolated worktree and stage only scoped integration files. |

## Out of Scope

- The separate `codex/audit` branch.
- Phase 6 Windows collector work and later roadmap phases.
- Terraform, cloud infrastructure, or remote telemetry.
- Installer and release workflow implementation; those are covered by the separate CI/CD design.

## Design Review Record

- Scope approved by the project owner on 2026-08-03.
- Branch ancestry, changed-path overlap, and conflict signals were inspected from the local Git
  repository before this document was written.
- Placeholder, consistency, ambiguity, required-section, and `git diff --check` reviews passed.
- Implementation tests were not run because this work item creates design documentation only; the
  required integration test commands are defined above for the implementation stage.
