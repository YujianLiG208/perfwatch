# CI/CD

Phase 6 continuous integration is implemented at `.github/workflows/ci.yml`. GitHub Actions runs
the workflow for pushes to `main` and pull requests targeting `main`.

The job topology is:

- `python-cpp-matrix`: four Windows-and-Ubuntu cells covering Python 3.11 and Python 3.12. Each
  cell builds C++ with CMake, runs CTest, and runs pytest.
- `python-cpp`: stable aggregator that succeeds only when the complete matrix succeeds.
- `frontend`: Node 24 job that runs the Vitest tests and the TypeScript/Vite production build.
- `quality`: Python 3.11 job that runs Ruff against the Python source and tests.

The workflow grants only `contents: read`, uses GitHub-owned actions, and cancels superseded runs
with a concurrency group scoped to each pull request or Git reference. The required branch checks
are `python-cpp`, `frontend`, and `quality`.

At documentation-capture time, the latest successful live validation run was:

- Run: https://github.com/YujianLiG208/perfwatch/actions/runs/32549128595
- Head SHA: `7779936240fe72095a922b5a955cdb8913be1877`

That run is historical evidence for workflow commit `7779936240fe72095a922b5a955cdb8913be1877`;
it is not evidence for the Phase 8 release workflow.

## Windows Release Workflow

`.github/workflows/release.yml` has two jobs. `build-windows` runs on `windows-latest` with Python
3.12 and Node 24, installs the pinned packaging dependencies, resolves Visual Studio, Ninja, Python,
and pybind11 paths, then executes the existing package build, explicit-mock smoke, and release archive
scripts. It uploads only the versioned ZIP and `.zip.sha256`, never the directory bundle.

The workflow accepts pushed tags matching `v*.*.*` and manual dispatch. Before building, it requires
the project version to be semantic; tag runs additionally require the exact `vMAJOR.MINOR.PATCH` tag
to equal `v` plus the version in `python/pyproject.toml`. Manual dispatch can build and upload the two
artifacts but cannot run the `publish` job.

Only `publish` receives `contents: write`. It uses the repository `GITHUB_TOKEN`, downloads the build
artifact, and invokes `gh release create` for these unsigned Windows x64 files:

- `perfwatch-0.1.0-windows-x64.zip`
- `perfwatch-0.1.0-windows-x64.zip.sha256`

No PAT or signing secret is required. Build, smoke, version, or archive failure prevents publication.
The checksum verifies integrity but not publisher identity. The committed workflow must reach GitHub
before manual dispatch can use it, and tag publication requires a tag containing that workflow.
Local static inspection does not claim a remote workflow run or published release.

Local sandbox validation used Ninja with MSVC, an explicit `pybind11_DIR`, and Vitest threads.
Those accommodations address the local sandbox environment and are not CI requirements.
