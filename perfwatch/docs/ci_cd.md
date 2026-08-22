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

Successful live validation evidence:

- Run: https://github.com/YujianLiG208/perfwatch/actions/runs/32549128595
- Head SHA: `7779936240fe72095a922b5a955cdb8913be1877`

Packaging and release automation remain deferred to Phase 8.

Local sandbox validation used Ninja with MSVC, an explicit `pybind11_DIR`, and Vitest threads.
Those accommodations address the local sandbox environment and are not CI requirements.
