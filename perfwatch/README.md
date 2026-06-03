# perfwatch

perfwatch is a Phase 1 skeleton for a cross-platform performance and energy monitoring tool.
It is planned as a hybrid C++/Python project: C++ for low-overhead collection interfaces and
Python for orchestration, analytics, SQLite persistence, and a local API.

## Current Status

Phase 1 only. The repository contains project initialization, deterministic mock data,
compile-safe C++ placeholders, Python package scaffolding, SQLite schema/writer skeletons,
FastAPI endpoints, CI/Docker development configuration, and minimal tests.

## Architecture Overview

- Native C++ layer: data structs, collector interface, deterministic `MockCollector`, and optional
  `perfwatch_native` pybind11 module.
- Python layer: native import fallback, deterministic Python mock collector, minimal analytics,
  SQLite writer, and FastAPI service.
- Storage: local SQLite tables for system samples, process samples, and events.
- Future UI: dashboard and overlay directories are placeholders only.

## What Works Now

- `GET /health` returns `{"status": "ok"}`.
- `GET /snapshot` returns deterministic mock snapshot data.
- SQLite schema initialization and insertion of one mock snapshot.
- Minimal C++ tests for deterministic mock data.
- Minimal Python tests for mock collection, analytics, storage, and API behavior.

## Intentionally Not Implemented Yet

- Real Linux `/proc` or `/sys` collection.
- Real Windows PDH/WMI collection.
- GPU collection.
- Transparent overlay.
- Full web dashboard.
- Complex battery prediction.
- Installer or release packaging.

## Local Setup

Python:

```bash
cd perfwatch/python
python -m venv .venv
# activate the venv for your shell
pip install -e ".[dev]"
pytest
```

API:

```bash
cd perfwatch/python
uvicorn perfwatch.api.app:app --reload
```

C++:

```bash
cd perfwatch
cmake -S cpp -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

Docker development:

```bash
cd perfwatch
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml run --rm dev
```

Docker is for development and testing only. It is not the production runtime for reading host
hardware sensors.

## Engineering Honesty

- Battery time is estimated from energy and discharge power inputs.
- Process energy score is an intentionally simple estimate, not a real measurement.
- CI cannot validate real hardware sensors.
- Docker cannot represent full host hardware access for production collection.
