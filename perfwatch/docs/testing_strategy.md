# Testing Strategy

Use the smallest check that protects each real product boundary.

## Automated checks

- Python tests cover mock/native selection, enrichment, SQLite migration and application queries,
  service lifecycle/error handling, API/WebSocket routes, runtime paths, and Overlay formatting.
- The C++ executable checks process CPU delta handling and one live Windows snapshot when running on
  Windows.
- Dashboard tests cover formatting, bounded history, initial/live data, reconnect with HTTP fallback,
  stale-response rejection, cleanup, and visible application states.
- The packaged smoke starts the explicit mock build, checks `/health`, `/snapshot`, and `/`, then
  verifies clean shutdown.
- Archive verification extracts the ZIP once and checks its required layout and native module.

## CI

Pull requests and `main` pushes run Python/C++ validation on Windows and Ubuntu with supported Python
versions, the Dashboard test/build gate, and Ruff. The release workflow builds the Windows package
and smoke-tests it before artifact upload or tag publication.

## Manual checks

Native sensor plausibility, AC transitions, Dashboard layout, Overlay topmost/click-through behavior,
display scaling, and packaged restart persistence require a physical interactive Windows session.
The durable Phase 9 result is summarized in
`Phase 9 Windows hardware and visual validation.md`.
