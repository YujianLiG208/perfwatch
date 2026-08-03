# Project CI/CD and Local Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three required CI check groups and publish tested Windows x64 and Linux x64 self-contained archives to GitHub Releases from validated version tags.

**Architecture:** Keep GitHub Actions in two workflows: CI validates Python/C++, frontend, and Ruff; Release builds the existing FastAPI/React application into a PyInstaller directory bundle on each target OS, smoke-tests it with the mock collector, archives it, and publishes only after both platforms succeed. FastAPI serves the production Vite output from the same localhost process, so the release needs no cloud service or second runtime.

**Tech Stack:** GitHub Actions, Python 3.11/3.12, FastAPI/Uvicorn, pytest, Ruff, C++17, CMake/CTest, pybind11, Node.js 22, React/Vite/Vitest, PyInstaller 6.21, GitHub CLI.

## Global Constraints

- Begin only after the Phase 3–5 integration plan completion gate passes and the integrated baseline is present on `origin/main`.
- Use `superpowers:using-git-worktrees` to create a clean `codex/cicd-pipeline` branch from the updated `origin/main`; do not continue CI/CD work on the merged integration branch.
- CI runners: `ubuntu-latest` and `windows-latest`; Python versions: `3.11` and `3.12`; frontend Node.js version: `22`.
- Release runners: `windows-latest` and `ubuntu-22.04`; release architecture: x64 only.
- Version tags must match `vMAJOR.MINOR.PATCH` exactly.
- Release artifacts must be `perfwatch-<version>-windows-x64.zip` and `perfwatch-<version>-linux-x64.tar.gz`, each with a SHA-256 sidecar.
- Manual `workflow_dispatch` runs build and smoke-test artifacts but never create a GitHub Release.
- Default workflow permission is `contents: read`; only the publish job receives `contents: write`.
- Use the repository `GITHUB_TOKEN`; do not add a personal access token.
- Do not add Terraform, cloud deployment, ARM, auto-update, MSI/MSIX, DEB/RPM, AppImage, signing, notarization, PyPI, npm publication, coverage gates, ESLint, or clang-tidy.
- Keep mock fallback behavior and do not require physical hardware in CI or release smoke tests.
- Follow the repository stage order for every task: Plan only, Implement visibly, Validate only, update the applicable process note, review the scoped diff, commit.
- Store workflow files at the Git repository root `.github/workflows/`; GitHub does not discover the existing nested `perfwatch/.github/workflows/` files.
- Run local Git commands from the Git repository root. Run project validation commands from the nested `perfwatch/` project root.

---

## File Map

### CI

- Create by moving: `.github/workflows/ci.yml` — three CI job groups, least privilege, and concurrency cancellation.
- Delete after move: `perfwatch/.github/workflows/ci.yml` — nested workflows are not discovered by GitHub.

### Production local application

- Modify: `perfwatch/python/src/perfwatch/api/app.py` — optional packaged dashboard mount.
- Create: `perfwatch/python/src/perfwatch/server.py` — localhost Uvicorn entry point.
- Modify: `perfwatch/python/pyproject.toml` — server script and packaging-only PyInstaller dependency.
- Modify: `perfwatch/python/tests/test_api.py` — static dashboard/API coexistence test.
- Create: `perfwatch/python/tests/test_server.py` — server argument delegation test.

### Native/package build

- Modify: `perfwatch/cpp/CMakeLists.txt` — install the optional native module into a packaging prefix.
- Create: `perfwatch/scripts/smoke_release.py` — standard-library health check for the built executable.
- Create by moving: `.github/workflows/release.yml` — validate, build, smoke-test, archive, checksum, and publish.
- Delete after move: `perfwatch/.github/workflows/release.yml` — nested workflows are not discovered by GitHub.

### Documentation

- Modify: `perfwatch/README.md` — CI status, source development, and archive startup instructions.
- Modify: `perfwatch/docs/ci_cd.md` — implemented CI/release behavior and limitations.
- Modify: `perfwatch/docs/testing_strategy.md` — frontend, Ruff, and packaged smoke coverage.
- Modify: `perfwatch/ui/dashboard/README.md` — same-origin packaged mode and Vite development mode.

---

### Task 0: Create the Isolated CI/CD Worktree

**Files:**

- No repository file changes.

**Interfaces:**

- Consumes: updated `origin/main` containing Phase 3–5.
- Produces: clean `codex/cicd-pipeline` worktree for every later task in this plan.

- [ ] **Step 1: Refresh and verify the integrated baseline**

Run from the original Git repository root:

```powershell
git fetch origin main
git merge-base --is-ancestor 8298574 origin/main
git merge-base --is-ancestor 27db3f6 origin/main
git merge-base --is-ancestor 780dd05 origin/main
```

Expected: fetch succeeds and all three ancestry commands exit 0.

- [ ] **Step 2: Invoke the required worktree skill**

Use `superpowers:using-git-worktrees` to create branch `codex/cicd-pipeline` from `origin/main`. Follow that skill's directory selection and safety checks rather than inventing another worktree location.

- [ ] **Step 3: Verify the isolated worktree**

Run in the new worktree:

```powershell
git branch --show-current
git status --short
git merge-base --is-ancestor origin/main HEAD
```

Expected: branch is `codex/cicd-pipeline`, status is empty, and HEAD descends from the updated `origin/main`.

---

### Task 1: Replace the Skeleton CI with Three Required Check Groups

**Files:**

- Create by moving: `.github/workflows/ci.yml`
- Delete after move: `perfwatch/.github/workflows/ci.yml`

**Interfaces:**

- Consumes: integrated Python tests, CMake/CTest suite, frontend package lock/scripts, and Ruff in `python[dev]`.
- Produces: check groups `python-cpp`, `frontend`, and `quality` for branch protection.

- [ ] **Step 1: Capture the local pre-change validation baseline**

Run from `perfwatch/`:

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

Expected: every command passes before workflow-only changes begin.

- [ ] **Step 2: Move the workflow to the repository root**

Run from the Git repository root:

```powershell
New-Item -ItemType Directory -Path .github/workflows -Force | Out-Null
git mv perfwatch/.github/workflows/ci.yml .github/workflows/ci.yml
```

Expected: Git records one rename and the workflow now occupies GitHub's required root directory.

- [ ] **Step 3: Replace `ci.yml` with the exact workflow**

Write `.github/workflows/ci.yml` as:

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
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  python-cpp:
    name: python-cpp / ${{ matrix.os }} / py${{ matrix.python-version }}
    runs-on: ${{ matrix.os }}
    defaults:
      run:
        working-directory: perfwatch
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.11", "3.12"]
    steps:
      - name: Check out repository
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: perfwatch/python/pyproject.toml

      - name: Install Python dependencies
        run: python -m pip install -e "python[dev]" pybind11

      - name: Configure C++
        run: cmake -S cpp -B build

      - name: Build C++
        run: cmake --build build --config Release

      - name: Run C++ tests
        run: ctest --test-dir build --output-on-failure -C Release

      - name: Run Python tests
        run: python -m pytest python/tests

  frontend:
    name: frontend
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: perfwatch
    steps:
      - name: Check out repository
        uses: actions/checkout@v6

      - name: Set up Node.js
        uses: actions/setup-node@v6
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: perfwatch/ui/dashboard/package-lock.json

      - name: Install frontend dependencies
        run: npm --prefix ui/dashboard ci

      - name: Run frontend tests
        run: npm --prefix ui/dashboard test

      - name: Build frontend
        run: npm --prefix ui/dashboard run build

  quality:
    name: quality
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: perfwatch
    steps:
      - name: Check out repository
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: perfwatch/python/pyproject.toml

      - name: Install Python dependencies
        run: python -m pip install -e "python[dev]"

      - name: Run Ruff
        run: python -m ruff check python/src python/tests
```

- [ ] **Step 4: Check the workflow diff and retained commands**

Run:

```powershell
git diff --check -- .github/workflows/ci.yml perfwatch/.github/workflows/ci.yml
rg -n "python-cpp|frontend|quality|pytest|ctest|ruff|npm.*test|npm.*run build|contents: read" .github/workflows/ci.yml
```

Expected: no whitespace errors and every required job/command/permission appears.

- [ ] **Step 5: Re-run the commands represented by the workflow**

Run:

```powershell
python -m pytest python/tests
python -m ruff check python/src python/tests
npm --prefix ui/dashboard test
npm --prefix ui/dashboard run build
ctest --test-dir build --output-on-failure -C Release
```

Expected: PASS. GitHub-hosted Windows/Linux matrix execution is validated in Task 5 after push.

- [ ] **Step 6: Review and commit the CI workflow move**

Run:

```powershell
git add .github/workflows/ci.yml perfwatch/.github/workflows/ci.yml
git diff --cached --check
git diff --cached
git commit -m "ci: validate backend frontend and quality"
```

Expected: one workflow-only commit that records the nested file deletion and root workflow creation.

---

### Task 2: Add the Packaged Local Server and Static Dashboard

**Files:**

- Create: `perfwatch/python/src/perfwatch/server.py`
- Modify: `perfwatch/python/src/perfwatch/api/app.py`
- Modify: `perfwatch/python/pyproject.toml`
- Create: `perfwatch/python/tests/test_server.py`
- Modify: `perfwatch/python/tests/test_api.py`

**Interfaces:**

- Consumes: `perfwatch.api.app.app`, Phase 5 API/WebSocket routes, and Vite output supplied at package time.
- Produces: `perfwatch.server.main(argv: Sequence[str] | None = None) -> None`, console script `perfwatch-server`, and `create_app(..., dashboard_directory: Path | None = None) -> FastAPI`.

- [ ] **Step 1: Write the failing server delegation test**

Create `perfwatch/python/tests/test_server.py`:

```python
from perfwatch.api.app import app
from perfwatch.server import main


def test_server_passes_bind_arguments_to_uvicorn(monkeypatch) -> None:
    called: dict[str, object] = {}

    def fake_run(application, *, host: str, port: int) -> None:
        called.update(application=application, host=host, port=port)

    monkeypatch.setattr("perfwatch.server.uvicorn.run", fake_run)

    main(["--host", "127.0.0.1", "--port", "8765"])

    assert called == {
        "application": app,
        "host": "127.0.0.1",
        "port": 8765,
    }
```

- [ ] **Step 2: Write the failing static dashboard/API coexistence test**

Add to `perfwatch/python/tests/test_api.py`:

```python
def test_packaged_dashboard_is_served_without_hiding_api_routes(tmp_path) -> None:
    dashboard_directory = tmp_path / "dashboard"
    dashboard_directory.mkdir()
    (dashboard_directory / "index.html").write_text(
        "<main>packaged dashboard</main>",
        encoding="utf-8",
    )
    app = create_app(
        settings=Settings(
            database_path=tmp_path / "packaged.sqlite3",
            snapshot_interval_seconds=0.01,
            use_mock_collector=True,
        ),
        collector=MockCollector(),
        dashboard_directory=dashboard_directory,
    )

    with TestClient(app) as client:
        dashboard_response = client.get("/")
        health_response = client.get("/health")

    assert dashboard_response.status_code == 200
    assert "packaged dashboard" in dashboard_response.text
    assert health_response.json() == {"status": "ok"}
```

- [ ] **Step 3: Run both tests to verify they fail**

Run:

```powershell
python -m pytest python/tests/test_server.py python/tests/test_api.py::test_packaged_dashboard_is_served_without_hiding_api_routes -v
```

Expected: FAIL because `perfwatch.server` and the `dashboard_directory` argument do not exist.

- [ ] **Step 4: Add the minimal server entry point**

Create `perfwatch/python/src/perfwatch/server.py`:

```python
from __future__ import annotations

import argparse
from collections.abc import Sequence

import uvicorn

from perfwatch.api.app import app


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the local perfwatch dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Mount packaged static assets after API/WebSocket routes**

Modify `perfwatch/python/src/perfwatch/api/app.py` with these imports and helper:

```python
from pathlib import Path
import sys

from fastapi.staticfiles import StaticFiles


def _bundled_dashboard_directory() -> Path | None:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root is None:
        return None
    dashboard_directory = Path(bundle_root) / "dashboard"
    if not (dashboard_directory / "index.html").is_file():
        return None
    return dashboard_directory
```

Add the optional argument to `create_app`:

```python
dashboard_directory: Path | None = None,
```

After both routers are included, mount only an existing dashboard directory:

```python
if dashboard_directory is not None:
    application.mount(
        "/",
        StaticFiles(directory=dashboard_directory, html=True),
        name="dashboard",
    )
```

Create the module-level packaged app with:

```python
app = create_app(dashboard_directory=_bundled_dashboard_directory())
```

- [ ] **Step 6: Declare the server script and packaging dependency**

In `perfwatch/python/pyproject.toml`, keep runtime dependencies unchanged and add:

```toml
[project.optional-dependencies]
dev = [
    "ruff",
    "mypy",
]
package = [
    "pyinstaller==6.21.0",
]

[project.scripts]
perfwatch = "perfwatch.cli:main"
perfwatch-server = "perfwatch.server:main"
```

Do not add PyInstaller to runtime dependencies.

- [ ] **Step 7: Run the targeted tests and quality check**

Run:

```powershell
python -m pip install -e "python[dev,package]"
python -m pytest python/tests/test_server.py python/tests/test_api.py -v
python -m ruff check python/src python/tests
```

Expected: all server/API tests and Ruff pass.

- [ ] **Step 8: Review and commit the packaged server boundary**

Run:

```powershell
git add python/src/perfwatch/server.py python/src/perfwatch/api/app.py python/pyproject.toml python/tests/test_server.py python/tests/test_api.py
git diff --cached --check
git diff --cached
git commit -m "feat: serve packaged local dashboard"
```

Expected: one focused application-boundary commit.

---

### Task 3: Make the Native Module Installable and Build a Local Directory Bundle

**Files:**

- Modify: `perfwatch/cpp/CMakeLists.txt`
- Create: `perfwatch/scripts/smoke_release.py`

**Interfaces:**

- Consumes: `perfwatch_native`, `perfwatch.server`, dashboard `dist/`, and `python[package]`.
- Produces: `build/native-install/perfwatch_native*`, `dist/perfwatch/`, and a cross-platform executable health smoke check.

- [ ] **Step 1: Prove the native target has no install rule**

Run:

```powershell
cmake -S cpp -B build
cmake --build build --config Release
cmake --install build --config Release --prefix build/native-install
```

Expected before the change: configure/build succeed but `build/native-install` does not contain `perfwatch_native`.

- [ ] **Step 2: Add the native install rule**

Inside the existing `if(pybind11_FOUND)` block in `perfwatch/cpp/CMakeLists.txt`, after linking the module, add:

```cmake
install(
    TARGETS perfwatch_native
    LIBRARY DESTINATION .
    RUNTIME DESTINATION .
)
```

- [ ] **Step 3: Rebuild and verify the installed native module**

Run:

```powershell
cmake -S cpp -B build
cmake --build build --config Release
cmake --install build --config Release --prefix build/native-install
Get-ChildItem -LiteralPath build/native-install
```

Expected: the install directory contains one platform-native `perfwatch_native` extension.

- [ ] **Step 4: Create the executable smoke checker**

Create `perfwatch/scripts/smoke_release.py`:

```python
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen


def wait_for_health(process: subprocess.Popen[str], url: str, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            raise RuntimeError(f"perfwatch exited before becoming healthy:\n{output}")
        try:
            with urlopen(url, timeout=1) as response:
                payload = json.load(response)
            if payload == {"status": "ok"}:
                return
        except (OSError, URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(0.25)
    raise TimeoutError(f"perfwatch did not become healthy at {url}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    port = 8765

    with tempfile.TemporaryDirectory() as temporary_directory:
        environment = os.environ.copy()
        environment["PERFWATCH_USE_MOCK_COLLECTOR"] = "true"
        environment["PERFWATCH_DATABASE_PATH"] = str(
            Path(temporary_directory) / "smoke.sqlite3"
        )
        process = subprocess.Popen(
            [str(args.executable), "--host", "127.0.0.1", "--port", str(port)],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            wait_for_health(process, f"http://127.0.0.1:{port}/health", 20)
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Build the production dashboard for same-origin API calls**

Run in PowerShell from `perfwatch/`:

```powershell
$env:VITE_API_BASE_URL = "/"
npm --prefix ui/dashboard ci
npm --prefix ui/dashboard run build
```

Expected: `ui/dashboard/dist/index.html` exists. The WebSocket default remains `/ws/snapshot`.

- [ ] **Step 6: Build the local PyInstaller directory bundle**

Run:

```powershell
python -m pip install -e "python[package]" pybind11
python -m PyInstaller --noconfirm --clean --onedir --name perfwatch --paths python/src --paths build/native-install --hidden-import perfwatch_native --add-data "ui/dashboard/dist:dashboard" --add-data "python/src/perfwatch/storage/schema.sql:perfwatch/storage" python/src/perfwatch/server.py
Copy-Item -LiteralPath README.md -Destination dist/perfwatch/README.md
Copy-Item -LiteralPath LICENSE -Destination dist/perfwatch/LICENSE
```

Expected: `dist/perfwatch/` contains the executable, runtime files, dashboard, schema, README, and LICENSE.

- [ ] **Step 7: Smoke-test the directory bundle**

Run on Windows:

```powershell
python scripts/smoke_release.py dist/perfwatch/perfwatch.exe
```

Run on Linux:

```bash
python scripts/smoke_release.py dist/perfwatch/perfwatch
```

Expected: the checker receives `{"status":"ok"}` and terminates the packaged service cleanly.

- [ ] **Step 8: Run focused source validation**

Run:

```powershell
python -m pytest python/tests/test_server.py python/tests/test_api.py -v
python -m ruff check python/src python/tests scripts/smoke_release.py
ctest --test-dir build --output-on-failure -C Release
```

Expected: all checks pass.

- [ ] **Step 9: Review and commit native/package support**

Run:

```powershell
git add cpp/CMakeLists.txt scripts/smoke_release.py
git diff --cached --check
git diff --cached
git commit -m "build: package native local application"
```

Expected: one build-support commit; generated `build/`, `dist/`, and dashboard `dist/` remain ignored and uncommitted.

---

### Task 4: Replace the Release Placeholder with Tag Builds and GitHub Releases

**Files:**

- Create by moving: `.github/workflows/release.yml`
- Delete after move: `perfwatch/.github/workflows/release.yml`

**Interfaces:**

- Consumes: valid version tag or manual dispatch, `python[package]`, CMake install target, Vite build, and `scripts/smoke_release.py`.
- Produces: two platform archives plus SHA-256 files; creates a GitHub Release only for a valid tag after both builds pass.

- [ ] **Step 1: Move the release workflow to the repository root**

Run from the Git repository root:

```powershell
git mv perfwatch/.github/workflows/release.yml .github/workflows/release.yml
```

Expected: Git records one rename into the already-created root workflow directory.

- [ ] **Step 2: Replace `release.yml` with the exact workflow**

Write `.github/workflows/release.yml` as:

```yaml
name: Release

on:
  push:
    tags: ["v*"]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  validate:
    name: validate-version
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
      publish: ${{ steps.version.outputs.publish }}
    steps:
      - name: Validate version source
        id: version
        shell: pwsh
        run: |
          if ("${{ github.event_name }}" -eq "workflow_dispatch") {
            "version=manual-${{ github.run_number }}" >> $env:GITHUB_OUTPUT
            "publish=false" >> $env:GITHUB_OUTPUT
            exit 0
          }
          $tag = "${{ github.ref_name }}"
          if ($tag -notmatch '^v\d+\.\d+\.\d+$') {
            throw "Release tag must match vMAJOR.MINOR.PATCH: $tag"
          }
          "version=$($tag.Substring(1))" >> $env:GITHUB_OUTPUT
          "publish=true" >> $env:GITHUB_OUTPUT

  build:
    name: build / ${{ matrix.platform }}
    needs: validate
    strategy:
      fail-fast: false
      matrix:
        include:
          - platform: windows-x64
            os: windows-latest
            executable: dist/perfwatch/perfwatch.exe
            extension: zip
          - platform: linux-x64
            os: ubuntu-22.04
            executable: dist/perfwatch/perfwatch
            extension: tar.gz
    runs-on: ${{ matrix.os }}
    defaults:
      run:
        working-directory: perfwatch
    steps:
      - name: Check out repository
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: perfwatch/python/pyproject.toml

      - name: Set up Node.js
        uses: actions/setup-node@v6
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: perfwatch/ui/dashboard/package-lock.json

      - name: Install frontend dependencies
        run: npm ci
        working-directory: perfwatch/ui/dashboard

      - name: Build packaged dashboard
        run: npm run build
        working-directory: perfwatch/ui/dashboard
        env:
          VITE_API_BASE_URL: /

      - name: Install packaging dependencies
        run: python -m pip install -e "python[package]" pybind11

      - name: Build and install native module
        run: |
          cmake -S cpp -B build
          cmake --build build --config Release
          cmake --install build --config Release --prefix build/native-install

      - name: Build application directory
        shell: pwsh
        run: |
          python -m PyInstaller `
            --noconfirm `
            --clean `
            --onedir `
            --name perfwatch `
            --paths python/src `
            --paths build/native-install `
            --hidden-import perfwatch_native `
            --add-data "ui/dashboard/dist:dashboard" `
            --add-data "python/src/perfwatch/storage/schema.sql:perfwatch/storage" `
            python/src/perfwatch/server.py
          Copy-Item -LiteralPath README.md -Destination dist/perfwatch/README.md
          Copy-Item -LiteralPath LICENSE -Destination dist/perfwatch/LICENSE

      - name: Smoke-test packaged application
        run: python scripts/smoke_release.py ${{ matrix.executable }}

      - name: Create archive and checksum
        shell: pwsh
        env:
          VERSION: ${{ needs.validate.outputs.version }}
          PLATFORM: ${{ matrix.platform }}
          EXTENSION: ${{ matrix.extension }}
        run: |
          New-Item -ItemType Directory -Path release -Force | Out-Null
          $archive = "perfwatch-$env:VERSION-$env:PLATFORM.$env:EXTENSION"
          $archivePath = Join-Path release $archive
          if ($env:RUNNER_OS -eq "Windows") {
            Compress-Archive -Path dist/perfwatch -DestinationPath $archivePath
          } else {
            tar -C dist -czf $archivePath perfwatch
          }
          $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archivePath).Hash.ToLowerInvariant()
          "$hash  $archive" | Set-Content -Encoding ascii "$archivePath.sha256"

      - name: Upload platform artifact
        uses: actions/upload-artifact@v6
        with:
          name: release-${{ matrix.platform }}
          path: perfwatch/release/*
          if-no-files-found: error

  publish:
    name: publish-release
    if: needs.validate.outputs.publish == 'true'
    needs: [validate, build]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Download platform artifacts
        uses: actions/download-artifact@v6
        with:
          pattern: release-*
          merge-multiple: true
          path: release

      - name: Create GitHub Release
        shell: pwsh
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          $assets = Get-ChildItem -LiteralPath release -File | ForEach-Object FullName
          gh release create $env:GITHUB_REF_NAME @assets --generate-notes --verify-tag
```

- [ ] **Step 3: Check release invariants locally**

Run:

```powershell
git diff --check -- .github/workflows/release.yml perfwatch/.github/workflows/release.yml
rg -n "workflow_dispatch|vMAJOR.MINOR.PATCH|ubuntu-22.04|windows-latest|smoke_release|sha256|contents: write|gh release create" .github/workflows/release.yml
```

Expected: no whitespace errors and every release safety invariant appears.

- [ ] **Step 4: Verify the manual path cannot publish**

Inspect the job expressions together:

```powershell
rg -n "publish=false|publish=true|if: needs.validate.outputs.publish" .github/workflows/release.yml
```

Expected: manual dispatch writes `publish=false`, tag validation writes `publish=true`, and the publish job requires the true output.

- [ ] **Step 5: Review and commit the release workflow move**

Run:

```powershell
git add .github/workflows/release.yml perfwatch/.github/workflows/release.yml
git diff --cached --check
git diff --cached
git commit -m "ci: publish tagged local application archives"
```

Expected: one release-workflow commit that records the nested file deletion and root workflow creation.

---

### Task 5: Document and Exercise the Implemented Pipeline

**Files:**

- Modify: `perfwatch/README.md`
- Modify: `perfwatch/docs/ci_cd.md`
- Modify: `perfwatch/docs/testing_strategy.md`
- Modify: `perfwatch/ui/dashboard/README.md`

**Interfaces:**

- Consumes: the implemented CI jobs, server entry point, package command, release workflow, and unsigned archive limitation.
- Produces: exact contributor and release instructions plus live GitHub workflow evidence from `codex/cicd-pipeline`.

- [ ] **Step 1: Update the documentation with exact implemented behavior**

Document these facts without promising unimplemented features:

```text
- CI runs python-cpp on Ubuntu/Windows with Python 3.11/3.12, frontend on Node 22, and Ruff on Python 3.11.
- Development mode keeps Vite on port 5173 and FastAPI on port 8000.
- Packaged mode serves the dashboard and API from one localhost Uvicorn process.
- workflow_dispatch builds artifacts but does not publish.
- vMAJOR.MINOR.PATCH tags publish unsigned Windows x64 and Linux x64 archives plus SHA-256 files.
- Physical hardware sensors, code signing, installers, ARM, and automatic updates are not covered.
```

Add the installed-server command:

```powershell
$env:PERFWATCH_USE_MOCK_COLLECTOR = "true"
perfwatch-server --host 127.0.0.1 --port 8000
```

- [ ] **Step 2: Run the full local validation gate**

Run:

```powershell
python -m ruff check python/src python/tests scripts/smoke_release.py
python -m pytest python/tests
cmake -S cpp -B build
cmake --build build --config Release
ctest --test-dir build --output-on-failure -C Release
npm --prefix ui/dashboard ci
npm --prefix ui/dashboard test
npm --prefix ui/dashboard run build
```

Expected: all checks pass with fresh output.

- [ ] **Step 3: Review and commit the documentation**

Run from the `perfwatch/` project root:

```powershell
git add README.md docs/ci_cd.md docs/testing_strategy.md ui/dashboard/README.md
git diff --cached --check
git diff --cached
git commit -m "docs: document local CI and release pipeline"
git status --short
```

Expected: a documentation-only commit and clean worktree.

- [ ] **Step 4: Push the implementation branch**

Run from the Git repository root:

```powershell
git push origin codex/cicd-pipeline
```

Expected: the remote branch contains the root workflows and all implementation/documentation commits.

- [ ] **Step 5: Open or update the pull request and verify CI**

Run:

```powershell
gh pr create --base main --head codex/cicd-pipeline --title "Add local CI and tagged releases" --body "Moves workflows to the repository root, adds backend/frontend/quality CI, and publishes tested Windows/Linux local application archives from version tags."
gh pr checks --watch
```

If a pull request already exists, replace `gh pr create` with `gh pr view --web` and use the existing pull request.

Expected: all four expanded Python/C++ matrix checks plus `frontend` and `quality` pass.

- [ ] **Step 6: Configure required checks after their names exist**

In GitHub repository settings for `main`, require:

```text
python-cpp / ubuntu-latest / py3.11
python-cpp / ubuntu-latest / py3.12
python-cpp / windows-latest / py3.11
python-cpp / windows-latest / py3.12
frontend
quality
```

Do not require `validate-version`, platform release builds, or `publish-release` for pull requests.

- [ ] **Step 7: Run the manual GitHub build verification after merge approval**

Wait for the owner to approve and merge the pull request to `main`. Do not merge it automatically. After the root release workflow exists on `main`, run:

```powershell
gh workflow run Release --ref main
$runId = gh run list --workflow Release --branch main --limit 1 --json databaseId --jq '.[0].databaseId'
gh run watch $runId
```

Expected: both platform build jobs pass, artifacts are available on the workflow run, and no GitHub Release is created.

---

## Plan Completion Gate

- A pull request runs all four Python/C++ matrix entries, frontend tests/build, and Ruff.
- `workflow_dispatch` creates both platform artifacts and no GitHub Release.
- A valid version tag creates both exact archive names and their SHA-256 files only after both smoke checks pass.
- The Windows archive runs on Windows with the mock collector.
- The Linux archive runs on Linux with the mock collector.
- Workflow permissions are read-only except for the final tag publish job.
- No Terraform, cloud deployment, long-lived credential, native installer, signing, ARM, or auto-update work is present.

## Primary References

- PyInstaller directory bundles and data inclusion: <https://pyinstaller.org/en/stable/usage.html>
- PyInstaller runtime data paths: <https://pyinstaller.org/en/stable/runtime-information.html>
- GitHub setup-python v6: <https://github.com/actions/setup-python>
- GitHub setup-node v6: <https://github.com/actions/setup-node>
- GitHub upload-artifact: <https://github.com/actions/upload-artifact>
- GitHub workflow discovery at repository root: <https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows>

## Plan Review Record

- Reviewed against `Project CI-CD design.md` on 2026-08-03.
- Verified coverage for Python/C++, frontend, Ruff, version validation, manual non-publishing builds, Windows/Linux archives, checksums, smoke tests, least privilege, and GitHub Releases.
- Corrected the implementation path so workflows move from `perfwatch/.github/workflows/` to the Git repository root `.github/workflows/`, which GitHub requires for discovery.
- Verified that `perfwatch.server`, `create_app`, CMake install output, PyInstaller input paths, artifact paths, and workflow consumers use consistent names.
- Placeholder and trailing-whitespace scans passed.
- No workflow, package, or release test was run while writing this plan; all executable validation commands are assigned to implementation tasks above.
