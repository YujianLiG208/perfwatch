# Scope

## In Scope for MVP

- Cross-platform project skeleton with C++ and Python boundaries.
- Mock-first collection pipeline.
- SQLite persistence for system and process samples.
- FastAPI local API with health and snapshot endpoints.
- Minimal tests for deterministic mock behavior.
- Fixture-based parser tests in later phases.

## Out of Scope for MVP

- Transparent overlay.
- Installer and release packaging.
- Complex battery prediction.
- Full dashboard implementation.
- Production-grade GPU adapter coverage.

## Engineering Honesty

perfwatch must clearly distinguish measured values from estimated values. In Phase 1 all snapshot
values are deterministic mock values. Battery remaining time and process energy score should be
described as estimated, not measured.
