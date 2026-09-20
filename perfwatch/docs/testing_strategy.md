# Testing Strategy

Use the smallest check that protects each real product boundary.

## Automated checks

- Python tests cover mock/native selection, enrichment, SQLite migration and application queries,
  service lifecycle/error handling, API/WebSocket routes, runtime paths, and Overlay formatting.
- The C++ executable checks process CPU delta handling and one live Windows snapshot when running on
  Windows, with assertions enabled in both Debug and Release builds.
- Dashboard tests cover formatting, bounded history, initial/live data, reconnect with HTTP fallback,
  stale-response rejection, cleanup, and visible application states.
- The packaged smoke starts the explicit mock build, checks `/health`, `/snapshot`, and `/`, then
  verifies clean shutdown. Its child uses a temporary `LOCALAPPDATA` directory, cleaned after child
  shutdown even on failure, so smoke samples do not enter the user's database.
- Archive verification extracts the ZIP once and checks its required layout and native module.

## CI

Pull requests and `main` pushes select Python/C++, Dashboard, and Ruff checks by changed paths; see
`ci_cd.md` for the mapping. Selected backend checks retain the Windows/Ubuntu and Python 3.11/3.12
matrix. Python-only edits skip native compilation unless the dependency configuration changes.
The release workflow builds the Windows package and smoke-tests it before artifact upload or tag
publication.

During implementation, run the affected test file or focused check, then its relevant final gate.
Rebuild and smoke-test the Windows package for packaging/native dependency or runtime changes and
release preparation. Changes limited to documentation or unrelated formatting do not require a full
package rebuild. Repeat checks only after relevant edits, failures, or new evidence.

## Manual checks

Native sensor plausibility, AC transitions, Dashboard layout, Overlay topmost/click-through behavior,
display scaling, and packaged restart persistence require a physical interactive Windows session.
The durable Phase 9 result is summarized in
`Phase 9 Windows hardware and visual validation.md`.
