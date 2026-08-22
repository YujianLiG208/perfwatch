# Phase 6 CI Completion Design

**Status:** Approved

**Date:** 2026-08-21

**Scope authority:** `README.md` and `docs/roadmap.md`

## Purpose

Complete the repository's continuous-integration gate for the existing Phase 1-5 baseline. Phase
6 validates Python, C++, the React dashboard, and Ruff on GitHub-hosted runners. It does not build
or publish an application release.

## Current Baseline

- The Git repository root is the parent of the `perfwatch/` project directory.
- The owner removed the two obsolete nested workflow files before this design was written:
  `perfwatch/.github/workflows/ci.yml` and `perfwatch/.github/workflows/release.yml`.
- GitHub currently discovers no workflows because no workflow exists at the repository root.
- GitHub Actions is enabled and restricted to GitHub-owned actions.
- The default `GITHUB_TOKEN` permission is read-only, Actions cannot approve pull requests, and the
  repository has no Actions secrets.
- `main` is the default branch. Required checks remain intentionally unconfigured until the new
  check names have completed successfully at least once.

## Goals

- Run Python and C++ validation on Windows and Ubuntu with Python 3.11 and 3.12.
- Require the native `perfwatch_native` CMake target to exist and build in every matrix entry.
- Run dashboard tests and the production build with Node.js 24 LTS.
- Run the existing Ruff rules as the only dedicated Python quality gate.
- Expose exactly three stable branch-protection checks: `python-cpp`, `frontend`, and `quality`.
- Limit workflow permissions to `contents: read` and cancel superseded runs for the same pull
  request or Git reference.
- Record live GitHub Actions evidence before marking Phase 6 complete.

## Non-Goals

- Release workflows, packages, archives, checksums, installers, or GitHub Releases.
- A production application entry point or static dashboard serving; those belong to Phase 7.
- Windows hardware collection, overlay work, or production packaging; those belong to Phase 8.
- Codecov, ESLint, mypy, clang-tidy, actionlint, Dependabot, or another quality service.
- Docker, self-hosted runners, cloud infrastructure, deployment, repository secrets, or PATs.
- A Node.js 26 CI matrix or exact Node patch pin.
- Fixes for Codex sandbox-specific process environment behavior.

## Considered Structures

### Selected: One CI Workflow with a Stable Matrix Gate

Create one root workflow containing the Python/C++ matrix, a matrix summary job, the frontend job,
and the Ruff job. The summary job gives branch protection one stable `python-cpp` name even when
the internal matrix changes.

This keeps triggers, permissions, and concurrency in one file while avoiding required checks tied
to individual operating-system and Python-version labels.

### Rejected: Three Separate Workflows

Separate Python/C++, frontend, and quality workflows would duplicate triggers, permissions, and
concurrency configuration without providing useful isolation at the current project size.

### Rejected: Require Every Matrix Context Directly

Requiring all four matrix contexts would avoid the summary job but make branch protection depend on
the exact matrix labels. A later supported-version change could leave `main` waiting for a retired
check name.

## Workflow Architecture

Create `.github/workflows/ci.yml` with workflow name `CI`.

### Triggers

- `pull_request` targeting `main`.
- `push` to `main`.
- No path filters. Every required check must report for every pull request targeting `main`.
- No `merge_group` trigger because the repository does not use a merge queue.

### Permissions

Set workflow-level permissions to:

```yaml
permissions:
  contents: read
```

No job receives a permission override. The workflow uses only GitHub-owned actions already allowed
by the repository:

- `actions/checkout@v7`
- `actions/setup-python@v7`
- `actions/setup-node@v7`

### Concurrency

Use one concurrency group per workflow and pull request or Git reference, with
`cancel-in-progress: true`. A newer commit on the same pull request or branch cancels its obsolete
run without cancelling unrelated branches.

## Jobs and Data Flow

### `python-cpp-matrix`

Run with `fail-fast: false` across:

| Dimension | Values |
| --- | --- |
| Runner | `windows-latest`, `ubuntu-latest` |
| Python | `3.11`, `3.12` |
| CMake configuration | `Release` |

Each entry:

1. Checks out the repository.
2. Sets up the matrix Python version and pip cache keyed by
   `perfwatch/python/pyproject.toml`.
3. Installs `perfwatch/python[dev]` and the existing CI build dependency `pybind11`.
4. Configures and builds `perfwatch/cpp` in Release mode.
5. Explicitly builds target `perfwatch_native`. This makes missing Python development files or an
   undiscovered pybind11 package a failure instead of a silent optional skip.
6. Runs CTest with failure output.
7. Runs `python -m pytest perfwatch/python/tests`.

The workflow does not upload the native module or other build outputs.

### `python-cpp`

This is the stable matrix summary job. It:

- Depends on `python-cpp-matrix`.
- Uses `if: always()` so it reports even when a matrix entry fails or is cancelled.
- Runs on `ubuntu-latest` without checkout or dependency installation.
- Passes only when `needs.python-cpp-matrix.result` is `success`.

Branch protection requires this job rather than the individual matrix labels.

### `frontend`

Run once on `ubuntu-latest`:

1. Check out the repository.
2. Set up Node.js major version `24` with npm caching keyed by
   `perfwatch/ui/dashboard/package-lock.json`.
3. Run `npm ci` in `perfwatch/ui/dashboard`.
4. Run the existing default `npm test` command.
5. Run `npm run build`, which performs both TypeScript checks and the Vite production build.

Node 24 is the Phase 6 LTS baseline. The workflow does not add Node 26 as a second matrix entry.

### `quality`

Run once on `ubuntu-latest` with Python 3.11:

1. Check out the repository.
2. Set up Python with the same pyproject-based pip cache.
3. Install `perfwatch/python[dev]`.
4. Run `python -m ruff check perfwatch/python/src perfwatch/python/tests`.

No second Python linter or C++ static analyzer is added.

## Failure Behavior

- A failing matrix entry does not cancel sibling matrix entries; all platform evidence remains
  visible.
- The `python-cpp` summary fails unless the complete matrix succeeds.
- pytest, CTest, native-target build, Ruff, frontend tests, and frontend production build all use
  their native nonzero exit status. No validation step uses `continue-on-error`.
- A cancelled superseded run is expected and is not reused as acceptance evidence.
- No failure path publishes an artifact, changes repository state, or receives write permission.
- Environment and tool failures during local work follow `perfwatch/AGENTS.md`: stop, report the
  exact command and error, and wait for owner authorization before changing strategy.

## Local Validation Constraints

The Codex Windows sandbox has two confirmed environment differences that must not leak into the
GitHub workflow:

- It exposes both `PATH` and `Path`. MSBuild's .NET process launcher rejects those duplicate
  case-insensitive keys. Local C++ validation therefore uses the Visual Studio Developer Shell,
  Ninja, and the same MSVC compiler.
- Vitest fork workers can time out in the sandbox. Local sandbox validation therefore uses
  `npm test -- --pool=threads`; the default `npm test` passes in the owner's normal PowerShell and
  remains the GitHub CI command.

The Python runtime also returns a quoted pybind11 CMake directory because the user path contains a
space. Local sandbox validation may pass `pybind11_DIR` explicitly. GitHub runners must build the
explicit `perfwatch_native` target using their normal setup-python paths.

These are validation accommodations, not application or workflow requirements.

## Repository File Scope

### Create

- `.github/workflows/ci.yml`: the complete CI workflow.

### Preserve as Absent

- `perfwatch/.github/workflows/ci.yml`: removed by the owner before implementation.
- `perfwatch/.github/workflows/release.yml`: removed by the owner before implementation; release
  automation remains deferred to Phase 8.

### Update After Live CI Evidence

- `perfwatch/README.md`: mark Phase 6 complete and describe the implemented checks.
- `perfwatch/docs/roadmap.md`: move Phase 6 into the completed baseline.
- `perfwatch/docs/ci_cd.md`: document jobs, permissions, concurrency, required checks, commands,
  and the successful Actions run.
- `perfwatch/docs/Project CI-CD design.md`: mark its Phase 6 release scope as superseded; retain its
  packaging concepts only as non-authoritative Phase 8 reference material.

### Do Not Modify

- Python, C++, API, dashboard source, or tests.
- `python/pyproject.toml`, `ui/dashboard/package.json`, or `package-lock.json`.
- Release, packaging, installer, or deployment files.

## Validation and Rollout

### Static Review

- Confirm `.github/workflows/ci.yml` exists at the Git repository root.
- Confirm the two nested workflow paths remain absent.
- Run `git diff --check`.
- Inspect the workflow for the exact triggers, matrix values, Node version, stable check names,
  commands, `contents: read`, and concurrency cancellation.
- Confirm it contains no release publication, artifact upload, secret use, or write permission.

No new YAML parser dependency is introduced. GitHub's workflow parser and live run provide the
authoritative syntax validation.

### Local Execution

Run fresh local evidence for:

- `python -m pytest python/tests`
- `python -m ruff check python/src python/tests`
- CMake configure, native build, and CTest through the documented sandbox Ninja/MSVC accommodation
- `npm test -- --pool=threads`
- `npm run build`

### Live GitHub Validation

1. Review and commit the scoped implementation locally.
2. Obtain explicit authorization before pushing or creating/updating a pull request.
3. Push `codex/phase6-cicd` and run CI through a pull request targeting `main`.
4. Confirm all four Python/C++ matrix entries, `python-cpp`, `frontend`, and `quality` pass.
5. Confirm repository Actions settings remain restricted and the workflow token remains read-only.
6. The owner configures `python-cpp`, `frontend`, and `quality` as required checks on `main` only
   after GitHub has reported those exact names.
7. Read back branch protection and record the successful Actions run URL in `docs/ci_cd.md`.
8. Update README and Roadmap only after live CI and required-check verification pass.

## Acceptance Criteria

Phase 6 is complete only when:

- GitHub discovers the root `CI` workflow.
- Pull requests and pushes to `main` trigger it.
- All four Python/C++ matrix entries pass and build `perfwatch_native`.
- CTest and pytest pass on Windows and Ubuntu with Python 3.11 and 3.12.
- The Node 24 frontend test and production-build job passes.
- The Ruff job passes with the existing rules.
- The workflow has `contents: read`, uses only GitHub-owned actions, and cancels superseded runs.
- `main` requires exactly `python-cpp`, `frontend`, and `quality` from GitHub Actions.
- No release workflow, release artifact, application dependency, or out-of-scope product feature is
  added.
- Project documentation matches the live repository state and includes the validation evidence.

## Design Review Record

- The owner approved the workflow architecture, data flow, failure handling, file scope, validation
  process, Node 24 LTS baseline, and acceptance criteria in chat on 2026-08-21.
- Local Python, Ruff, MSVC/Ninja, CTest, pybind11 native-module, Vitest-thread, and Vite production
  validation passed before this design was finalized.
- GitHub repository permissions, Actions restrictions, secrets, default branch, and current branch
  rules were read back successfully before this design was finalized.
- Release publication remains deferred to Phase 8 as required by the current README and Roadmap.
