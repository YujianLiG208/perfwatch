# Roadmap

Phases 1-6 are complete and form the current mock-driven baseline.

## Platform Priority

Windows is the only near-term runtime, validation, and release target because it is the physical
hardware environment available to the project owner.

- Live Linux collection is not scheduled in Phases 6-9. The existing fixture-tested parsers and
  compile-safe boundaries are retained only as a **Future long-term plan for Linux**.
- GPU vendor-specific adapters are not scheduled in Phases 6-9. The existing interface and
  unavailable fallback are retained only as a **Future Long-term plan for GPU adapter**.
- Phase 9 full-function acceptance covers the planned Windows product scope and intentionally
  excludes the deferred Linux runtime and GPU vendor-adapter work.

## Completed Baseline

1. Completed: project skeleton and deterministic mock pipeline.
2. Completed: Linux parser fixture layer, without live runtime collection.
3. Completed: SQLite persistence.
4. Completed: FastAPI backend service loop using mock/native-compatible collectors, without real
   hardware collection.
5. Completed: local Vite and React dashboard with current metrics, history charts, top processes,
   WebSocket updates, and HTTP fallback.
6. Completed: root GitHub Actions CI with a Windows-and-Ubuntu Python 3.11/3.12 matrix, Node 24
   frontend tests and production build, Ruff, `contents: read`, per-pull-request or Git-reference
   concurrency cancellation, and stable required checks `python-cpp`, `frontend`, and `quality`.

## Planned Phases

### Phase 7: Integrated Local Application

- Connect battery-runtime and process-energy scoring helpers to the sampling pipeline while keeping
  estimated values explicitly labeled.
- Replace the fixed mock timestamp and values with deterministic, evolving samples suitable for
  exercising history charts.
- Add one production entry point that serves the FastAPI API and built dashboard together, so the
  API and frontend no longer need to be started separately.

### Phase 8: Windows Product Features

- Implement live Windows CPU, memory, battery, and process collection using appropriate native,
  PDH, or WMI paths. GPU vendor-specific collection remains deferred.
- Implement the desktop transparent overlay against the local service.
- Add production runtime assembly and Windows packaging, including the application, dashboard
  assets, SQLite schema, required native files, release artifact, and checksum publication.

### Phase 9: Windows Hardware and Visual Validation

- Validate the application on the project owner's physical Windows laptop, including sensor
  availability, sampling stability, persistence, API/WebSocket behavior, and fallback handling.
- Perform browser visual validation for the dashboard and desktop visual validation for the
  transparent overlay.
- Run the packaged Windows application through the complete flow: collect, estimate, persist,
  query, stream, display, overlay, shut down, and restart.

Phase 9 is complete only when the packaged application can complete this full planned workflow on
Windows. Linux runtime collection and GPU vendor adapters remain explicitly outside that gate.

## Future Long-term Work

- **Future long-term plan for Linux:** connect the existing parsers to live `/proc` and `/sys`
  collection only when Linux hardware and a dedicated validation environment become available.
- **Future Long-term plan for GPU adapter:** add vendor-specific GPU collection only when suitable
  hardware and repeatable validation are available.
