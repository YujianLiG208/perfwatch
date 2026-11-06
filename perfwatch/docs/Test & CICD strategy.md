# Testing and CI/CD

Protect real product boundaries with the smallest effective check.

## Testing Guardrails (Anti-Over-Testing)

- **Windows-Only Target**: PerfWatch targets Windows exclusively. Do not add cross-platform fallback branches or tests for non-Windows environments.
- **No Standalone Formatting or Helper Unit Tests**: String/number formatting, runtime path resolution, and UI label states must be verified inside existing route, window, or component integration tests rather than dedicated micro-unit tests.
- **Observable Behavior Only**: Assert final outputs, persisted records, and rendered states; do not assert internal mock call counts or private helper execution.
- **Targeted Local Execution**: During development, run only the test suite affected by the change. Rebuild and smoke-test the full Windows package only when modifying packaging configurations, native dependencies, or runtime entrypoints.

---

## Automated Checks

- **Python (`python/tests`)**: Covers mock/native collector selection, battery and process-energy enrichment, SQLite schema migration/queries/rollback, service lifecycle, HTTP/WebSocket routes, and live Win32 Overlay window creation and cleanup.
- **C++ (`perfwatch_cpp_tests`)**: Validates process CPU delta calculation and a live Windows snapshot. Test files undefine `NDEBUG` before `<cassert>` so assertions remain active in both Debug and Release builds.
- **Dashboard (`ui/dashboard`)**: Vitest suite covering bounded 60-point history, WebSocket streaming with HTTP polling fallback, stale-response cancellation, unmount cleanup, and error/unavailable UI states.
- **Packaged Smoke Check**: Extracts the built Windows `.zip` archive once and runs `perfwatch.exe --mock` using an isolated temporary `LOCALAPPDATA` directory (cleaned up automatically on exit or failure) to verify archive layout, service startup, endpoint response, and clean shutdown in a single pass.

## Manual Hardware & Visual Checks

Physical Windows sessions are required to verify hardware sensor plausibility, AC/battery power transitions, Dashboard and Overlay visual layout, DPI scaling, Overlay topmost/click-through behavior, and restart persistence.

---

## Continuous Integration (`.github/workflows/ci.yml`)

Triggered on pushes to `main` and pull requests targeting `main`. The workflow runs with `contents: read` permission and cancels superseded runs per PR or Git ref.

### Path-Scoped Selection (`scripts/ci_scope.py`)

The `changes` job compares the checkout against the PR base or previous push SHA (including renames and deletions) to select jobs:

| Changed Paths | Selected Checks |
| :--- | :--- |
| Markdown (`*.md`) only | None (skips all product checks) |
| `ui/dashboard/**` | `frontend` (Vitest + TypeScript/Vite production build) |
| `python/**` (code & tests) | `quality` (Ruff) + `python-cpp-matrix` (pytest only; skips C++ build) |
| `cpp/**` or `python/pyproject.toml` | `quality` + `python-cpp-matrix` (pytest + pybind11 C++ extension & CTest) |
| `.pre-commit-config.yaml` | `quality` (Ruff) |
| Workflows, `scripts/**`, `packaging/**` | All checks (`frontend`, `quality`, and full native `python-cpp-matrix`) |

### Job Topology

- **`python-cpp-matrix`**: Runs `pytest` across Python 3.11 and Python 3.12 on Windows. When native checks are selected, it installs `pybind11`, compiles both the C++ test executable and the Python native extension, and runs `CTest`.
- **`python-cpp`**: Required branch status aggregator; succeeds when change detection passes and the matrix either succeeds or is intentionally skipped.
- **`frontend`**: Node 24 job running Vitest and the Vite production build (required status check).
- **`quality`**: Python 3.11 job installing only Ruff to lint Python source, tests, and scripts (required status check).

Unselected jobs are skipped at the job level so the required `python-cpp`, `frontend`, and `quality` status checks never remain pending.

---

## Windows Release Workflow (`.github/workflows/release.yml`)

Triggered by `v*.*.*` tags or manual `workflow_dispatch`:

1. **`build-windows`**: Runs on `windows-latest` (Python 3.12, Node 24), installs pinned packaging dependencies, builds the native extension, Dashboard, and PyInstaller bundle, executes the isolated packaged smoke check, and uploads the versioned `perfwatch-<version>-windows-x64.zip` artifact.
2. **`publish`**: Runs only on tag pushes where `vMAJOR.MINOR.PATCH` matches the version in `python/pyproject.toml`. Grants `contents: write` to the default `GITHUB_TOKEN` and runs `gh release create` to publish the unsigned Windows x64 `.zip` archive.