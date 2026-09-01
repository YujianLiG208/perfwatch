# Roadmap

Phases 1-9 are complete and form the current Windows product baseline.

## Platform Priority

Windows is the only near-term runtime, validation, and release target because it is the physical
hardware environment available to the project owner.

- Live Linux collection is not scheduled in Phases 6-9. The existing fixture-tested parsers and
  compile-safe boundaries are retained only as a **Future long-term plan for Linux**.
- GPU vendor-specific adapters are not scheduled in Phases 6-9. The existing interface and
  unavailable fallback are retained only as a **Future Long-term plan for GPU adapter**.
- Phase 9 full-function acceptance covered the planned Windows product scope and intentionally
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
7. Completed Phase 7 feature scope:
   - deterministic evolving mock timestamps and values;
   - battery-runtime and process-energy enrichment through persistence, API/WebSocket, and Dashboard;
   - one production entry point serving the FastAPI API and built Dashboard together.
8. Completed Phase 8 Windows product scope:
   - live nullable CPU, memory, battery, and process collection through native Windows APIs;
   - a topmost click-through Win32 Overlay implemented with Python `ctypes`, User32, and GDI;
   - a PyInstaller 6.22.2 directory application with explicit mock selection and LocalAppData
     persistence;
   - a verified unsigned Windows x64 ZIP and lowercase SHA-256 file;
   - a tag-gated GitHub Actions workflow that builds on Windows and publishes only matching semantic
     version tags. Manual dispatch builds artifacts without publishing.

Phase 7D is the documentation and full-acceptance closeout for these three feature deliveries. It is
not a fourth Phase 7 feature.

## Completed Phase 9

### Phase 9: Windows Hardware and Visual Validation

- Validated the application on the project owner's physical Windows laptop, including sensor
  availability, sampling stability, persistence, API/WebSocket behavior, and fallback handling.
- Completed browser visual validation for the dashboard and desktop visual validation for the
  transparent overlay.
- Ran the packaged Windows application through the complete flow: collect, estimate, persist,
  query, stream, display, overlay, shut down, and restart.

The packaged application completed the full planned workflow on the project owner's Windows laptop.
Linux runtime collection and GPU vendor adapters remain explicitly outside the completed gate. See
`Phase 9 Windows hardware and visual validation.md` for the recorded evidence.

## Future Long-term Work

- **Future long-term plan for Linux:** connect the existing parsers to live `/proc` and `/sys`
  collection only when Linux hardware and a dedicated validation environment become available.
- **Future Long-term plan for GPU adapter:** add vendor-specific GPU collection only when suitable
  hardware and repeatable validation are available.
