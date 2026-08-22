# Project CI/CD Design

> **Phase 6 status notice:** This legacy design is superseded where it conflicts with the
> authoritative Phase 6 design at
> `docs/superpowers/specs/2026-08-21-phase-6-ci-completion-design.md`. The implemented workflow is
> `.github/workflows/ci.yml`. Release, packaging, publication, and signing material below is future
> Phase 8 design input, not implemented Phase 6 behavior.

**Status:** Approved design

**Date:** 2026-08-03

**Prerequisite:** Phase 3–5 integration has passed its acceptance criteria and is merged to `main`.

## Purpose

Provide repeatable validation for the Python, C++, and Phase 5 frontend code, then publish
versioned Windows and Linux application archives from Git tags. This design is intentionally local
application CI/CD: it does not provision or deploy cloud infrastructure.

## Current Baseline

The repository already contains:

- A GitHub Actions CI matrix for Ubuntu and Windows with Python 3.11 and 3.12.
- CMake build and CTest execution.
- Python pytest execution.
- A Phase 5 frontend with npm lockfile, Vitest tests, TypeScript checks, and a Vite build.
- A manually triggered release workflow that currently prints a placeholder message.

The current CI does not run the frontend or an explicit quality check. The current release workflow
does not build or publish artifacts.

## Goals

- Validate every pull request and every push to `main`.
- Cover Python/C++ behavior on Windows and Linux.
- Validate Phase 5 frontend tests and production compilation.
- Add the smallest useful code-quality gate.
- Build versioned Windows x64 and Linux x64 application archives from version tags.
- Publish both archives and their checksums to GitHub Releases.
- Keep workflow permissions minimal and prevent a partial platform build from publishing a release.

## Non-Goals

- Terraform or any cloud provider.
- Deployment to a hosted API or dashboard.
- ARM builds.
- MSI, MSIX, DEB, RPM, AppImage, or other native installers.
- Automatic client updates.
- Code signing or notarization.
- PyPI or npm publication.
- Coverage thresholds, ESLint, clang-tidy, or other additional quality systems.

## Workflow Structure

Retain two workflow files:

- `.github/workflows/ci.yml` for pull-request and `main` validation.
- `.github/workflows/release.yml` for tag-triggered builds and GitHub Releases.

Separate reusable workflows and custom composite actions are not needed at the current project size.

## CI Workflow

### Triggers and concurrency

Run CI for:

- `pull_request` targeting `main`.
- `push` to `main`.

Use one concurrency group per workflow and Git reference, cancelling an older in-progress run when a
new commit supersedes it. Grant the workflow only `contents: read`.

### Job 1: `python-cpp`

Use the existing operating-system and Python matrix:

| Dimension | Values |
| --- | --- |
| Runner | `ubuntu-latest`, `windows-latest` |
| Python | `3.11`, `3.12` |
| CMake configuration | `Release` |

Each matrix entry performs:

1. Checkout.
2. Python setup with pip caching.
3. Installation of the Python package with development dependencies and `pybind11`.
4. CMake configure and Release build.
5. CTest with failure output.
6. Python pytest.

This repeats the C++ build across Python versions, but keeps the existing, easily understood matrix.
Split or reduce it only if measured Actions time becomes a cost.

### Job 2: `frontend`

Run once on `ubuntu-latest` with Node.js 22 and npm caching:

1. Checkout.
2. Node setup.
3. `npm ci` in `ui/dashboard`.
4. `npm test`.
5. `npm run build`.

The build command already runs TypeScript checks before Vite, so a separate TypeScript job would be
duplicate work.

### Job 3: `quality`

Run once on `ubuntu-latest` with Python 3.11:

1. Checkout.
2. Python setup with pip caching.
3. Install the package development dependencies.
4. Run `python -m ruff check python/src python/tests`.

Ruff is already declared as a development dependency. Do not add another linter until a concrete
gap appears. C++ compilation and the frontend TypeScript build remain their respective minimum
static correctness gates.

### Required checks

Configure `python-cpp`, `frontend`, and `quality` as required checks on `main`. Branch-protection
configuration is a one-time GitHub repository setting, not Terraform or application code.

## Release Prerequisites

Phase 5 is currently a development-mode split application: the CLI prints one snapshot, FastAPI is
started through Uvicorn, and Vite serves the dashboard separately. A useful application archive
therefore requires a minimal production packaging path before the release workflow can succeed:

- Add a production service entry point that starts the local FastAPI application.
- Build the dashboard once and serve its static output from the local FastAPI process.
- Include the optional native `perfwatch_native` module when its platform build succeeds.
- Keep mock fallback behavior so the packaged application remains testable without hardware access.
- Package the application with PyInstaller in directory mode rather than a single executable.

Directory mode is selected because native modules and dashboard assets are explicit, startup does
not require extraction to a temporary directory, and the result can still be distributed as one
compressed archive.

## Release Workflow

### Trigger and version validation

Trigger on pushed tags matching `v*`. Before building, validate that the tag is exactly
`vMAJOR.MINOR.PATCH`, where each component is a non-negative integer. An invalid tag fails before
artifact creation.

The workflow also exposes `workflow_dispatch` for build verification, but a manually triggered
run must not create a GitHub Release because it has no approved version tag.

### Build jobs

Use a two-entry matrix:

| Runner | Artifact |
| --- | --- |
| `windows-latest` | `perfwatch-<version>-windows-x64.zip` |
| `ubuntu-22.04` | `perfwatch-<version>-linux-x64.tar.gz` |

Pin Linux packaging to Ubuntu 22.04 instead of `ubuntu-latest` so a future runner-image update does
not silently raise the minimum glibc baseline.

Each build entry performs:

1. Checkout the tag.
2. Set up Python and Node.js 22.
3. Install locked frontend dependencies and build the dashboard.
4. Install Python packaging dependencies and `pybind11`.
5. Configure and build the native module in Release mode.
6. Build a directory-mode PyInstaller application containing Python code, the native module, the
   SQLite schema, and dashboard static files.
7. Run a packaged-application smoke check using the mock collector.
8. Create the platform archive and SHA-256 checksum.
9. Upload the archive and checksum as workflow artifacts.

### Publish job

The publish job:

- Depends on both platform build jobs.
- Runs only for a valid version tag.
- Uses `ubuntu-latest`.
- Downloads all platform artifacts.
- Receives `contents: write`; all other jobs remain `contents: read`.
- Creates one GitHub Release with the tag, generated release notes, both archives, and checksum
  files using the GitHub CLI available on the runner.

Because publication waits for every matrix build, a Windows or Linux build failure prevents release
creation rather than publishing an incomplete release.

## Artifact Contents

Each platform archive contains:

```text
perfwatch/
├── perfwatch executable
├── native runtime files
├── dashboard static assets
├── SQLite schema
├── README.md
└── LICENSE
```

The first release is explicitly unsigned. Release notes and the README must state that limitation.
Signing becomes required before the project is promoted as a broadly distributed end-user binary.

## Failure and Recovery Behavior

- CI failure blocks merging through required checks.
- A matrix build failure prevents the publish job from starting.
- A packaged smoke-check failure prevents archive upload.
- Re-running a failed tag workflow must reuse the same source tag; changing source requires a new
  version tag.
- If GitHub Release creation partially fails, remove the incomplete draft/release through GitHub and
  rerun the unchanged tag workflow after correcting the external failure.
- Never move an already published version tag to different source code.

## Security Boundaries

- Default every workflow to `contents: read`.
- Grant `contents: write` only to the final publish job.
- Use the automatically scoped `GITHUB_TOKEN`; do not add a personal access token.
- Install frontend packages with `npm ci` and the committed lockfile.
- Do not execute release publication for pull requests or manually supplied arbitrary refs.
- Do not place signing credentials in the repository. If signing is added later, use protected
  environment secrets and explicit release approval.

## Validation Strategy

### CI workflow

- Validate YAML structure locally where tooling is available.
- Open a pull request and confirm all matrix entries plus `frontend` and `quality` execute.
- Confirm a deliberate failing test blocks its corresponding check before enabling branch protection.

### Release workflow

- Run `workflow_dispatch` to exercise build and smoke-test steps without publication.
- Create the first valid version tag only after both platform artifacts pass manual inspection.
- Download the release assets on Windows and Linux, verify checksums, and launch each archive with
  the mock collector.

## Acceptance Criteria

- Pull requests and `main` pushes run all three CI job groups.
- Python/C++ checks pass on both supported operating systems and Python versions.
- Frontend tests and production build run in CI.
- Ruff is enforced without introducing another linter.
- Manual release verification cannot publish a GitHub Release.
- A valid version tag produces both named platform archives and SHA-256 checksums.
- Publication occurs only after both platform builds and smoke checks succeed.
- Release assets start with the mock collector on their target operating systems.
- Workflows contain no Terraform, cloud deployment, or long-lived credential configuration.

## Implementation Order

1. Complete and validate Phase 3–5 integration.
2. Extend CI and make the three job groups green on the integrated codebase.
3. Add the minimal production service/static-dashboard entry point.
4. Add and validate directory-mode packaging on Windows and Linux.
5. Replace the release placeholder with tag build and publish jobs.
6. Configure required checks on `main` after the workflow names are stable.

## Design Review Record

- Scope approved by the project owner on 2026-08-03.
- The design was checked against the existing CI workflow, release placeholder, Phase 5 frontend
  scripts, and current application startup behavior.
- Placeholder, consistency, ambiguity, required-section, and `git diff --check` reviews passed.
- The review made manual `workflow_dispatch` build verification mandatory and explicitly prevented
  it from publishing a release.
- Implementation tests were not run because this work item creates design documentation only; CI,
  packaging, and release validation are defined above for their implementation stages.
