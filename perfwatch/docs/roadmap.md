# Roadmap

Phases 3-5 are integrated on `codex/phase-3-5-integration`. `main` contains
their separately merged histories; the integration conflict-resolution and
documentation commits remain on the integration branch until its pull request
is merged.

1. Completed: skeleton and mock pipeline.
2. Completed: Linux parser fixture layer, without real runtime collection.
3. Completed: SQLite persistence.
4. Completed: FastAPI backend service loop using mock/native-compatible collectors, without real
   hardware collection.
5. Completed: local Vite and React dashboard with current metrics, history charts, top processes,
   WebSocket updates, and HTTP fallback.
6. Windows collector.
7. GPU adapter.
8. Overlay.
9. Packaging.

Live Linux collection, Windows PDH/WMI collection, GPU adapters, the overlay,
and installers remain incomplete.
