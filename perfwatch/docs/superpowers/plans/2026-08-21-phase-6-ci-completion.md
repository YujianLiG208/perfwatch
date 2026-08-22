# Phase 6 CI Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan.

**Goal:** Complete Phase 6 by adding one repository-root GitHub Actions workflow that validates Python/C++ on Windows and Ubuntu with Python 3.11 and 3.12, validates the Node 24 frontend, enforces Ruff, and exposes the stable required checks `python-cpp`, `frontend`, and `quality`.

**Architecture:** A single `.github/workflows/ci.yml` owns all Phase 6 automation. A four-cell `python-cpp-matrix` performs the platform/runtime work and feeds one non-matrix `python-cpp` aggregation job; independent `frontend` and `quality` jobs provide the other stable branch-protection contexts. Release automation and packaging remain deferred to Phase 8.

**Tech Stack:** GitHub Actions, `actions/checkout@v7`, `actions/setup-python@v7`, `actions/setup-node@v7`, Python 3.11/3.12, CMake, CTest, pybind11, MSVC/GCC, Node.js 24, npm, Vitest, Vite, Ruff, pytest, GitHub CLI.

**Spec:** `perfwatch/docs/superpowers/specs/2026-08-21-phase-6-ci-completion-design.md`

## Global Constraints

- Run repository commands from the Git top level, `C:\Users\Yujian Li\Documents\Performance & Energy Monitor`, unless a step names another working directory. The application project is the `perfwatch` subdirectory.
- Remain on branch `codex/phase6-cicd`; do not merge or rewrite history.
- Preserve unrelated user changes. The user already deleted `perfwatch/.github/workflows/ci.yml` and `perfwatch/.github/workflows/release.yml`; do not issue a deletion command. Verify those paths are absent, then stage their already-existing deletions with the root-workflow commit so the remote repository records the move away from the nested workflows.
- Use Node.js 24 LTS in CI. Node.js 26 is not the Phase 6 baseline.
- Use only GitHub-owned actions already allowed by repository policy. Do not add Marketplace actions, secrets, artifacts, release jobs, package publication, coverage services, or new dependencies.
- Keep workflow permissions at `contents: read` and do not grant write permissions.
- Do not encode sandbox accommodations in GitHub Actions. The official workflow uses the normal CMake generator and normal `npm test`; Ninja, an explicit `pybind11_DIR`, and Vitest's threads pool are local sandbox validation accommodations only.
- Follow the project stage order for every material change: plan, implement visibly, validate, update the process note, review the Git diff, then commit.
- If an environment or tool command fails, stop at that exact command, report the error, and wait for explicit user authorization before retrying or changing strategy.
- Obtain explicit user authorization before each external write: pushing a branch, creating or updating a pull request, or changing GitHub branch protection.
- Never store a literal placeholder in committed documentation. Runtime evidence such as the successful GitHub Actions URL must be captured from `gh` and inserted as the actual value.

## Planned File Changes

- Create: `.github/workflows/ci.yml`
- Record the user's existing deletions in Git: `perfwatch/.github/workflows/ci.yml`
- Record the user's existing deletions in Git: `perfwatch/.github/workflows/release.yml`
- Update after successful live CI: `perfwatch/README.md`
- Update after successful live CI: `perfwatch/docs/roadmap.md`
- Update after successful live CI: `perfwatch/docs/ci_cd.md`
- Update after successful live CI: `perfwatch/docs/Project CI-CD design.md`
- This plan: `perfwatch/docs/superpowers/plans/2026-08-21-phase-6-ci-completion.md`

---

## Task 1: Commit the implementation plan

**Files:**

- Create: `perfwatch/docs/superpowers/plans/2026-08-21-phase-6-ci-completion.md`

### Step 1: Verify the plan is concrete and internally consistent

Run:

```powershell
Get-Content -Raw perfwatch\docs\superpowers\plans\2026-08-21-phase-6-ci-completion.md
$planMatches = rg -n "TBD|TODO|implement later|fill in|appropriate error handling|similar to Task|<[^>]+>" perfwatch\docs\superpowers\plans\2026-08-21-phase-6-ci-completion.md
$unexpectedPlanMatches = $planMatches | Where-Object { $_ -notmatch '^\d+:.*rg -n "' }
if ($unexpectedPlanMatches) { throw "Plan contains placeholder text: $($unexpectedPlanMatches -join '; ')" }
git diff --check -- perfwatch/docs/superpowers/plans/2026-08-21-phase-6-ci-completion.md
```

Expected: the complete plan is printed; the filtered placeholder scan produces no unexpected matches; `git diff --check` returns exit code 0 with no output.

### Step 2: Review and commit only the plan

Run:

```powershell
git status --short
git diff -- perfwatch/docs/superpowers/plans/2026-08-21-phase-6-ci-completion.md
git add -- perfwatch/docs/superpowers/plans/2026-08-21-phase-6-ci-completion.md
git diff --cached --check
git diff --cached --name-status
git commit -m "docs: plan phase 6 CI completion"
```

Expected: the cached name list contains only this plan before the commit. The two user-owned nested-workflow deletions remain unstaged.

---

## Task 2: Add the repository-root Phase 6 workflow

**Files:**

- Create: `.github/workflows/ci.yml`
- Record existing deletion: `perfwatch/.github/workflows/ci.yml`
- Record existing deletion: `perfwatch/.github/workflows/release.yml`

**Interfaces:**

- Triggers: pushes to `main` and pull requests targeting `main`
- Stable required-check contexts: `python-cpp`, `frontend`, `quality`
- Internal diagnostic matrix: `python-cpp-matrix (OS, Python version)`
- Existing test entry points: pytest, CMake/CTest, Vitest, Vite build, Ruff

### Step 1: Prove the root workflow is currently absent

Run:

```powershell
if (-not (Test-Path .github\workflows\ci.yml)) { throw "Expected failure: root Phase 6 workflow is absent" }
```

Expected: the command fails with `Expected failure: root Phase 6 workflow is absent`. This is the red test for the workflow location.

### Step 2: Verify the user's nested-workflow deletions without deleting anything

Run:

```powershell
if (Test-Path perfwatch\.github\workflows\ci.yml) { throw "Nested ci.yml still exists" }
if (Test-Path perfwatch\.github\workflows\release.yml) { throw "Nested release.yml still exists" }
git status --short -- perfwatch/.github/workflows/ci.yml perfwatch/.github/workflows/release.yml
```

Expected: both paths are absent and Git reports both as deleted.

### Step 3: Create the minimal root workflow

Create `.github/workflows/ci.yml` with exactly this content:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  python-cpp-matrix:
    name: python-cpp-matrix (${{ matrix.os }}, Python ${{ matrix.python-version }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.11", "3.12"]
    steps:
      - name: Check out repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: perfwatch/python/pyproject.toml

      - name: Install Python dependencies
        run: python -m pip install -e "perfwatch/python[dev]" pybind11

      - name: Configure C++
        run: cmake -S perfwatch/cpp -B perfwatch/build -DCMAKE_BUILD_TYPE=Release

      - name: Build C++ tests
        run: cmake --build perfwatch/build --config Release

      - name: Require native Python extension
        run: cmake --build perfwatch/build --config Release --target perfwatch_native

      - name: Run C++ tests
        run: ctest --test-dir perfwatch/build --build-config Release --output-on-failure

      - name: Run Python tests
        run: python -m pytest perfwatch/python/tests -q

  python-cpp:
    name: python-cpp
    needs: python-cpp-matrix
    if: ${{ always() }}
    runs-on: ubuntu-latest
    steps:
      - name: Verify Python and C++ matrix
        shell: bash
        run: test "${{ needs.python-cpp-matrix.result }}" = "success"

  frontend:
    name: frontend
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: perfwatch/ui/dashboard
    steps:
      - name: Check out repository
        uses: actions/checkout@v7

      - name: Set up Node.js
        uses: actions/setup-node@v7
        with:
          node-version: "24"
          cache: npm
          cache-dependency-path: perfwatch/ui/dashboard/package-lock.json

      - name: Install frontend dependencies
        run: npm ci

      - name: Run frontend tests
        run: npm test

      - name: Build frontend
        run: npm run build

  quality:
    name: quality
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: perfwatch/python/pyproject.toml

      - name: Install Python dependencies
        run: python -m pip install -e "perfwatch/python[dev]"

      - name: Run Ruff
        run: python -m ruff check perfwatch/python/src perfwatch/python/tests
```

### Step 4: Run fast static invariants

Run:

```powershell
$workflow = Get-Content -Raw .github\workflows\ci.yml
$required = @(
  'permissions:',
  'contents: read',
  'cancel-in-progress: true',
  'name: python-cpp',
  'name: frontend',
  'name: quality',
  'ubuntu-latest',
  'windows-latest',
  'python-version: ["3.11", "3.12"]',
  'node-version: "24"',
  'actions/checkout@v7',
  'actions/setup-python@v7',
  'actions/setup-node@v7',
  '--target perfwatch_native'
)
$missing = $required | Where-Object { -not $workflow.Contains($_) }
if ($missing) { throw "Missing workflow invariants: $($missing -join ', ')" }
$forbidden = @('pull_request_target:', 'permissions: write-all', 'actions/upload-artifact', 'release:', 'npm publish', 'merge_group:')
$present = $forbidden | Where-Object { $workflow.Contains($_) }
if ($present) { throw "Forbidden workflow content: $($present -join ', ')" }
```

Expected: exit code 0 and no output.

### Step 5: Validate Python locally

Run from the repository root:

```powershell
python -m pytest perfwatch/python/tests -q
python -m ruff check perfwatch/python/src perfwatch/python/tests
```

Expected: all pytest tests pass; Ruff reports `All checks passed!`.

### Step 6: Validate C++ and the native extension using the approved sandbox accommodations

Run from the Git top level in a fresh PowerShell process:

```powershell
& 'C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\Launch-VsDevShell.ps1' -Arch amd64 -HostArch amd64
$phase6Build = Join-Path ([IO.Path]::GetTempPath()) ("perfwatch-phase6-" + [guid]::NewGuid())
$pybind11Dir = (python -m pybind11 --cmakedir).Trim().Trim('"')
cmake -S perfwatch/cpp -B $phase6Build -G Ninja -DCMAKE_BUILD_TYPE=Release "-Dpybind11_DIR=$pybind11Dir"
cmake --build $phase6Build --target perfwatch_native perfwatch_cpp_tests
ctest --test-dir $phase6Build --output-on-failure
```

Expected: CMake configures with Ninja and MSVC, both targets build, and CTest reports 100% tests passed. Do not copy these sandbox accommodations into `.github/workflows/ci.yml`.

### Step 7: Validate the frontend using the approved sandbox pool accommodation

Run:

```powershell
Push-Location perfwatch\ui\dashboard
npm test -- --pool=threads
npm run build
Pop-Location
```

Expected: four Vitest files and twenty tests pass; Vite production build succeeds. The existing bundle-size warning is non-blocking. The workflow itself must retain plain `npm test`.

### Step 8: Review and commit the workflow plus the two confirmed deletions

Run:

```powershell
git diff --check
git status --short
git diff -- .github/workflows/ci.yml perfwatch/.github/workflows/ci.yml perfwatch/.github/workflows/release.yml
git add -- .github/workflows/ci.yml perfwatch/.github/workflows/ci.yml perfwatch/.github/workflows/release.yml
git diff --cached --check
git diff --cached --name-status
git commit -m "ci: add phase 6 validation workflow"
```

Expected: the cached diff contains one added root workflow and the two user-confirmed nested-workflow deletions, with no other files.

---

## Task 3: Run the workflow on GitHub and capture evidence

**Files:** None

**External state:** Branch push, pull request, GitHub Actions run

### Step 1: Obtain authorization and push the implementation commits

After the user explicitly authorizes the external write, run:

```powershell
git push -u origin codex/phase6-cicd
```

Expected: the branch is pushed successfully. If the push fails, stop without changing remotes, credentials, or history.

### Step 2: Reuse an existing pull request or create one only with authorization

Inspect first:

```powershell
gh pr list --head codex/phase6-cicd --base main --state open --json number,title,url,isDraft
```

If an open pull request exists, use it. If none exists, obtain explicit authorization and run:

```powershell
gh pr create --base main --head codex/phase6-cicd --title "Complete Phase 6 CI validation" --body "Implements the approved Phase 6 CI design: Python/C++ validation on Windows and Ubuntu for Python 3.11 and 3.12, Node 24 frontend test/build, Ruff quality gate, and stable required-check names." --draft
```

Expected: exactly one open pull request for the branch.

### Step 3: Wait for every live CI job

Run:

```powershell
gh pr checks codex/phase6-cicd --watch --interval 10
gh run list --workflow CI --branch codex/phase6-cicd --limit 1 --json databaseId,headSha,status,conclusion,url
```

Expected: all four matrix cells succeed, then `python-cpp`, `frontend`, and `quality` succeed. The latest run has conclusion `success` and its head SHA matches the pushed commit.

### Step 4: Confirm the workflow used the approved security posture

Run:

```powershell
gh api repos/YujianLiG208/perfwatch/actions/permissions
gh api repos/YujianLiG208/perfwatch/actions/permissions/selected-actions
gh api repos/YujianLiG208/perfwatch/actions/permissions/workflow
```

Expected:

- Actions are enabled with `allowed_actions` set to `selected`.
- GitHub-owned actions are allowed; verified and arbitrary pattern actions are not enabled.
- Default workflow permissions are read-only and pull requests cannot approve reviews.

---

## Task 4: Configure and verify the three required checks

**Files:** None

**External state:** Branch protection for `main`

### Step 1: Ask the repository owner to configure branch protection

After the first successful live CI run, ask the user to configure a branch protection rule for `main` with exactly these required status-check contexts:

```text
python-cpp
frontend
quality
```

Do not require `python-cpp-matrix` cells individually. Do not change merge, review, force-push, deletion, or administrator-bypass policies unless the user separately requests them.

### Step 2: Verify branch protection read-only

After the user confirms configuration, run outside the sandbox with read-only GitHub CLI authorization:

```powershell
gh api repos/YujianLiG208/perfwatch/branches/main/protection/required_status_checks
gh api repos/YujianLiG208/perfwatch/rulesets
```

Expected: either the branch-protection endpoint or an active ruleset targeting `main` requires exactly `python-cpp`, `frontend`, and `quality`. If both mechanisms exist, confirm they do not create contradictory or stale required contexts.

---

## Task 5: Update Phase 6 documentation from live evidence

**Files:**

- Modify: `perfwatch/README.md`
- Modify: `perfwatch/docs/roadmap.md`
- Modify: `perfwatch/docs/ci_cd.md`
- Modify: `perfwatch/docs/Project CI-CD design.md`

### Step 1: Capture a successful run URL and SHA; fail closed if it is not successful

Run:

```powershell
$phase6Run = gh run list --workflow CI --branch codex/phase6-cicd --limit 1 --json databaseId,headSha,status,conclusion,url | ConvertFrom-Json
if ($phase6Run.Count -ne 1) { throw "Expected exactly one latest CI run" }
if ($phase6Run.conclusion -ne 'success') { throw "Latest CI run is not successful: $($phase6Run.conclusion)" }
if ([string]::IsNullOrWhiteSpace($phase6Run.url)) { throw "Successful CI run URL is missing" }
$phase6Run | Format-List databaseId,headSha,status,conclusion,url
```

Expected: a non-empty successful run URL and the validated head SHA are printed. Use these exact values in `docs/ci_cd.md`; do not type a placeholder.

### Step 2: Update `perfwatch/README.md`

Make these exact semantic changes while preserving the document's current style:

- Change the implementation status from Phases 1-5 complete to Phases 1-6 complete.
- Add Phase 6 as completed: root GitHub Actions CI, Python/C++ Windows-and-Ubuntu Python 3.11/3.12 matrix, Node 24 frontend test/build, and Ruff.
- Keep Phases 7-9 as planned and keep release packaging in Phase 8.
- Remove any limitation claiming CI is missing or still planned.
- Name the stable required checks `python-cpp`, `frontend`, and `quality`.

### Step 3: Update `perfwatch/docs/roadmap.md`

Make these exact semantic changes:

- Move Phase 6 into the completed baseline.
- Record the validated matrix, frontend, Ruff, read-only permissions, concurrency cancellation, and stable check names.
- Leave Phase 7, Phase 8, and Phase 9 planned; do not move release work into Phase 6.

### Step 4: Update `perfwatch/docs/ci_cd.md` as the process note

Document:

- Workflow path `.github/workflows/ci.yml`.
- Trigger policy: push to `main` and pull requests targeting `main`.
- Job topology: four-cell `python-cpp-matrix`, stable `python-cpp` aggregator, `frontend`, and `quality`.
- Runtime/tool baselines: Python 3.11/3.12, Windows/Ubuntu, Node 24, CMake/CTest, pytest, Vitest/Vite, Ruff.
- Security and concurrency: `contents: read`, GitHub-owned actions only, per-PR/ref cancellation.
- Required branch checks: `python-cpp`, `frontend`, `quality`.
- Successful validation evidence: insert `$phase6Run.url` and `$phase6Run.headSha` as their actual captured values.
- Explicit deferral: packaging and release automation remain Phase 8 work.
- Local sandbox note: Ninja/MSVC, explicit `pybind11_DIR`, and Vitest threads were validation accommodations only and are not CI requirements.

### Step 5: Mark the legacy CI/CD design as superseded where it conflicts

At the top of `perfwatch/docs/Project CI-CD design.md`, add a status notice that:

- The authoritative Phase 6 design is `perfwatch/docs/superpowers/specs/2026-08-21-phase-6-ci-completion-design.md`.
- The implemented workflow is `.github/workflows/ci.yml`.
- Any release, packaging, publication, or signing material in the legacy document is future Phase 8 design input, not implemented Phase 6 behavior.

Do not delete the legacy document.

### Step 6: Validate documentation consistency

Run:

```powershell
rg -n "Phase 6|python-cpp|frontend|quality|Node(.js)? 24|Python 3.11|Python 3.12|Phase 8" perfwatch\README.md perfwatch\docs\roadmap.md perfwatch\docs\ci_cd.md "perfwatch\docs\Project CI-CD design.md"
rg -n "TBD|TODO|fill in|run URL here|commit SHA here|Node(.js)? 26" perfwatch\README.md perfwatch\docs\roadmap.md perfwatch\docs\ci_cd.md "perfwatch\docs\Project CI-CD design.md"
git diff --check -- perfwatch/README.md perfwatch/docs/roadmap.md perfwatch/docs/ci_cd.md "perfwatch/docs/Project CI-CD design.md"
```

Expected: the first search shows the new Phase 6 facts; the second search returns exit code 1 with no matches; `git diff --check` returns exit code 0.

### Step 7: Review and commit the documentation only

Run:

```powershell
git status --short
git diff -- perfwatch/README.md perfwatch/docs/roadmap.md perfwatch/docs/ci_cd.md "perfwatch/docs/Project CI-CD design.md"
git add -- perfwatch/README.md perfwatch/docs/roadmap.md perfwatch/docs/ci_cd.md "perfwatch/docs/Project CI-CD design.md"
git diff --cached --check
git diff --cached --name-status
git commit -m "docs: record phase 6 CI completion"
```

Expected: the cached diff contains exactly the four documentation files.

### Step 8: Obtain authorization, push the documentation commit, and revalidate CI

After explicit user authorization, run:

```powershell
git push
gh pr checks codex/phase6-cicd --watch --interval 10
```

Expected: all live checks pass again for the documentation commit.

---

## Task 6: Final verification and handoff

**Files:** None

### Step 1: Verify repository and GitHub state from fresh commands

Run:

```powershell
git status --short --branch
git log --oneline --decorate -5
git diff --check origin/main...HEAD
git diff --name-status origin/main...HEAD
gh pr checks codex/phase6-cicd
gh run list --workflow CI --branch codex/phase6-cicd --limit 1 --json headSha,status,conclusion,url
gh api repos/YujianLiG208/perfwatch/actions/permissions
gh api repos/YujianLiG208/perfwatch/actions/permissions/workflow
gh api repos/YujianLiG208/perfwatch/branches/main/protection/required_status_checks
```

Expected:

- The working tree is clean.
- The branch contains the approved design, this implementation plan, the root workflow, the two recorded nested-workflow deletions, and the four documentation updates only.
- The latest CI run succeeds for `HEAD`.
- `python-cpp`, `frontend`, and `quality` pass and are required for `main`.
- GitHub Actions policy remains selected GitHub-owned actions with read-only default permissions.
- No release workflow, artifact upload, package publication, secret, or source/dependency change was added.

### Step 2: Request code review

Invoke `superpowers:requesting-code-review` and review the complete diff against:

```text
perfwatch/docs/superpowers/specs/2026-08-21-phase-6-ci-completion-design.md
```

Resolve correctness findings with the same implement → validate → process note → diff review → commit sequence. Do not broaden Phase 6 for optional enhancements.

### Step 3: Hand off without merging

Report:

- Pull request URL.
- Latest successful CI URL and head SHA.
- Local validation results.
- Required-check verification result.
- Exact commits created.
- Any remaining non-blocking warnings, including the existing frontend bundle-size warning.

Do not merge the pull request. Ask the user whether they want to review and merge it or authorize a separate finishing workflow.
