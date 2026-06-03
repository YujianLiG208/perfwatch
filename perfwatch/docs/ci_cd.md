# CI/CD

GitHub Actions runs a skeleton-friendly matrix across `ubuntu-latest` and `windows-latest` with
Python 3.11 and 3.12.

The CI strategy is:

- Check out the repository.
- Set up Python.
- Install Python dependencies.
- Configure and build C++ with CMake.
- Run C++ tests through CTest.
- Run Python tests with pytest.

Release automation is intentionally a placeholder in Phase 1. Packaging is not implemented.
