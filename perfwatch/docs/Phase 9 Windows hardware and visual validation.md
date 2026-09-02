# Phase 9 Windows Acceptance

Phase 9 validated the packaged Windows application on the project owner's physical laptop. This
document retains durable acceptance facts only; command transcripts and machine-specific temporary
paths belong in task history rather than product documentation.

## Environment

- Windows 11 Pro x64 on a 1920 x 1080 display.
- Dashboard checked in Microsoft Edge at 125% and 100% display scaling.
- Unsigned Windows x64 directory bundle produced with PyInstaller 6.22.2.

## Accepted behavior

- Live CPU, memory, battery, and process samples updated continuously for 15 minutes.
- Unsupported CPU package power and temperature remained unavailable instead of becoming mock or
  zero values.
- AC disconnect and reconnect changed battery state without crashing the application.
- The Dashboard remained readable at full and compact widths, restored data after refresh, and
  maintained its live WebSocket connection.
- The Overlay remained topmost, readable, translucent, click-through, and non-activating at both
  tested display scales.
- Overlay waiting, live, and stale states followed service availability.
- Two packaged native runs reused one SQLite database; history grew across restart and shutdown
  completed cleanly.
- HTTP health, snapshot, metrics, and process routes plus the WebSocket stream and Dashboard all
  returned live packaged data.

## Release evidence

- Artifact: `perfwatch-0.1.0-windows-x64.zip`
- SHA-256: `22e74d3a192c83c9fa2c58292162616153c56b29b05fddc92e52c6970af98cd6`
- Python suite: 63 tests passed before the simplification audit.
- Dashboard suite: 27 tests passed before the simplification audit.
- Windows CTest: 1 test executable passed.

The checksum verifies artifact integrity, not publisher identity. The release remains unsigned.
