# Phase 9 Windows Hardware and Visual Validation

**Date:** 2026-08-26; completed 2026-09-01

**Status:** Complete; 9A-9E passed on the project owner's Windows laptop.

## Scope and ownership

- 9A environment and release-artifact baseline: Codex.
- 9B physical sensor, stability, and fallback validation: project owner.
- 9C Dashboard browser visual validation: project owner.
- 9D Overlay desktop visual and interaction validation: project owner.
- 9E packaged full-flow acceptance and documentation closeout: Codex after the owner reports 9B-9D results.

Phase 9 validates the packaged Windows product. It does not add Linux runtime collection, GPU
vendor adapters, a new sensor SDK, a browser automation framework, or another product feature.

## 9A environment and artifact baseline

The baseline was collected on the project owner's physical Windows laptop in an interactive desktop
session.

| Check | Observed result |
| --- | --- |
| Machine | Dell G7 7588, x64-based PC |
| Operating system | Windows 11 Pro 10.0.26200, build 26200, 64-bit |
| Desktop session | Interactive; Explorer and DWM running |
| Display | 1920 x 1080, 125% scaling, 120 DPI |
| Battery | Dell W7NKD82; status OK; 77% at 2026-08-26 23:32 PDT |
| Browser | Microsoft Edge installed; Codex browser control probe passed |
| Product data | `%LOCALAPPDATA%\PerfWatch` exists |
| Default port | `127.0.0.1:8000` available during the check |
| PowerShell | 7.6.4 |
| Python | 3.12.13 |
| Node/npm | Node 26.3.0; npm 11.16.0 |
| Native build tools | CMake 4.2.3; Ninja 1.13.2; MSVC toolsets 14.51.36231 and 14.52.36328 |
| Packaging boundary | PyInstaller 6.22.2 and pybind11 3.1.0 available |

The source environment also contains the declared FastAPI, Uvicorn, Pydantic, pytest, httpx,
websockets, Ruff, and mypy dependencies. Ninja remains an explicit build-script path rather than a
`PATH` command; this matches the Phase 8 build procedure.

No `perfwatch` process was running before extraction. The release checksum matched:

```text
1cdf2ad963a0a1bd170ffdc9569057b6deb0f65d426b7272fe2c0e8196d0290e  perfwatch-0.1.0-windows-x64.zip
```

A new Phase 9 acceptance copy was expanded to:

```text
C:\Users\Yujian Li\AppData\Local\Temp\perfwatch-phase9-c33ba06cfc1c4c5ea6164a8c723f0587\perfwatch
```

The fresh copy contains `perfwatch.exe`, README, LICENSE, Dashboard assets, the SQLite schema, and
exactly one `perfwatch_native.cp312-win_amd64.pyd`. Running `perfwatch.exe --help` from this copy
exited with code zero and exposed the expected public `--mock` and `--no-overlay` options.

## Owner manual run guide

Use ordinary PowerShell. Do not add `--mock`: Phase 9 must exercise the native Windows collector.

```powershell
$Phase9Product = 'C:\Users\Yujian Li\AppData\Local\Temp\perfwatch-phase9-c33ba06cfc1c4c5ea6164a8c723f0587\perfwatch'
Set-Location -LiteralPath $Phase9Product
.\perfwatch.exe
```

Wait for the console to print `PerfWatch Dashboard: http://127.0.0.1:8000/`, then open that address
in Edge. Keep the console open during 9B-9D. Use `Ctrl+C` for normal shutdown.

### 9B physical sensor, stability, and fallback checklist

Run the normal packaged application for at least 15 continuous minutes.

- [x] Startup completes without `startup failed` or an unexpected Overlay exit.
- [x] The Dashboard receives a live snapshot and keeps updating approximately once per second.
- [x] CPU usage becomes numeric after the initial rate-counter sample.
- [x] CPU frequency, used/total memory, battery percentage, and process rows are plausible.
- [x] Dashboard battery percentage agrees with the Windows battery indicator within one percentage point.
- [x] CPU and memory trends broadly follow Task Manager; exact instantaneous equality is not required.
- [x] Process names and the highest-load processes are plausible compared with Task Manager.
- [x] Charts continue advancing for 15 minutes without freezing, resetting unexpectedly, or moving backward in time.
- [x] The application remains responsive and does not terminate during the stability window.
- [x] Unsupported CPU package power or temperature remains `N/A`, not a fabricated zero.
- [x] Other available metrics continue updating when one or more measurements are `N/A`.
- [x] Disconnect AC power and confirm the battery state changes to discharging or an unavailable estimate without a crash.
- [x] Reconnect AC power and confirm the battery state returns to charging/connected behavior.
- [x] Remaining-time values, when present, are labelled as estimates; unavailable estimates remain clearly unavailable.

Record any missing sensor, repeated warning, frozen timestamp, implausible value, or crash as a failure
with the visible message and approximate time. A missing vendor-neutral power or temperature reading
alone is not a failure.

### 9C Dashboard browser visual checklist

Perform the first pass with Edge maximized at the native 1920 x 1080 display and 125% Windows scale.
Then make the browser roughly half-screen width for one compact-layout check.

- [x] The header, connection status, metric cards, charts, process table, and footer are all visible.
- [x] Connection status reaches `Live` and the last-updated value continues changing.
- [x] No card text overlaps, clips, or escapes its container.
- [x] Charts have readable labels and do not cover adjacent content.
- [x] The process table remains readable and aligned with long or changing process names.
- [x] `N/A`, `Not available`, and estimated-value wording are visually distinct and understandable.
- [x] The page has no unexpected horizontal overflow when maximized.
- [x] The compact-width pass remains usable without missing content.
- [x] Refreshing the page restores the current snapshot, recent history, process rows, and live stream.
- [x] Edge Developer Tools show no repeating uncaught error or WebSocket error while the application is healthy.

Capture one maximized screenshot and note any visible defect. Do not treat the existing Vite bundle-size
build advisory as a runtime visual failure.

### 9D Overlay desktop visual and interaction checklist

First use the normal packaged launch at the current 125% Windows scale.

- [x] The Overlay is fully inside the top-right work area and is not hidden beneath the taskbar.
- [x] All lines are readable; no text overlaps or is clipped.
- [x] The background is translucent while the text retains adequate contrast.
- [x] The Overlay remains visible above Edge and Notepad when either application is active.
- [x] Clicking within the Overlay bounds reaches a harmless control or blank Notepad document behind it.
- [x] The Overlay does not take keyboard focus when clicked through.
- [x] CPU, memory, battery, power, process, and freshness text agrees with the Dashboard state.
- [x] Unavailable values display as `N/A` and never as fabricated zeroes.

For explicit waiting and stale-state checks, first stop the normal application. Open two ordinary
PowerShell windows in the acceptance directory. Start the standalone Overlay child before the
service:

```powershell
.\perfwatch.exe --overlay-child --snapshot-url http://127.0.0.1:8000/snapshot
```

- [x] With no service running, the Overlay shows `Waiting for service`.

In the other PowerShell window start the packaged service without its managed Overlay:

```powershell
.\perfwatch.exe --no-overlay
```

- [x] The standalone Overlay changes from waiting to live values after the service starts.
- [x] After stopping the service with `Ctrl+C`, the Overlay keeps its last real values and marks them `STALE`.
- [x] Stop the standalone Overlay with `Ctrl+C`; it exits cleanly.

Finally, manually change Windows display scaling to 100%, relaunch the normal package, and repeat the
position/readability/topmost/click-through checks. Restore 125% scaling afterward.

- [x] The Overlay passes the same layout and interaction checks at 100% scale.
- [x] Windows scaling is restored to 125% after the check.

## Result handoff template

Send the following results back to Codex before 9E:

```text
9B: PASS or FAIL
15-minute stability duration completed:
Battery disconnect/reconnect result:
Unavailable sensor fields observed:
Sensor/stability notes:

9C: PASS or FAIL
Maximized and compact-width result:
Browser console notes:
Screenshot path or attachment:

9D: PASS or FAIL
125% result:
Waiting/live/stale result:
Topmost/click-through result:
100% result and 125% restoration:
Overlay notes:
```

Do not proceed to 9E when any item is marked FAIL. Report the failure first so it can be classified
as a separate focused repair task.

## 9B-9D owner acceptance result

On 2026-09-01 the project owner reported that the 9B sensor/stability checks, 9C Dashboard checks,
and 9D Overlay checks were complete. The only defect found during that pass was a transient battery
power value of `2147483.648 W` during an AC disconnect/reconnect sequence. Windows was returning the
`BATTERY_UNKNOWN_RATE` sentinel (`0x80000000`), which the collector had interpreted as a signed rate.

The Windows collector now treats that sentinel as unavailable at the collection boundary. After the
package was rebuilt, the owner repeated the power transition and confirmed that Energy Signals no
longer displayed the abnormal value and that an unknown rate displayed as `Unavailable`. All other
9B-9D checklist items had already passed. CPU package power and temperature remained unavailable on
this hardware as expected; this is an accepted vendor-neutral fallback, not a Phase 9 failure.

## 9E packaged full-flow acceptance

The corrected package used for final acceptance was:

```text
release\perfwatch-0.1.0-windows-x64.zip
SHA-256: 22e74d3a192c83c9fa2c58292162616153c56b29b05fddc92e52c6970af98cd6
Bytes: 40375541
```

Its checksum, extraction, executable, Dashboard, and single native-module layout checks passed. The
acceptance copy was expanded to:

```text
C:\Users\YUJIAN~1\AppData\Local\Temp\perfwatch-phase9e-36bac8f0719c4db08c34160ed84e164c\perfwatch
```

The packaged application was then run twice without `--mock`, using an isolated LocalAppData tree
and the same SQLite database. `--no-overlay` was used for this automated portion because the managed
and standalone Overlay lifecycle, visuals, topmost behavior, click-through behavior, stale state,
and DPI scaling had already passed the owner-run 9D checks.

| Evidence | First run | Restart |
| --- | ---: | ---: |
| Live timestamp | `1788252434282` | `1788252440305` |
| `/metrics/recent` rows returned | 3 | 7 |
| `/processes/top` rows returned | 10 | 10 |
| Persisted system rows | 4 | 8 |
| Persisted process rows | 40 | 80 |
| Battery power at probe | 16.188 W | 16.204 W |
| Graceful shutdown exit code | 0 | 0 |

Both runs returned HTTP 200 for health, snapshot, recent metrics, top processes, and Dashboard
requests. `/ws/snapshot` streamed the current native snapshot. Snapshot timestamps were current and
advanced across restart, the database retained the first run and continued growing, and no package
process remained afterward. The process energy field was present but unavailable because CPU package
power was unavailable. The four recorded events were the expected per-run warnings for unavailable
CPU package power and temperature.

### Final gates

| Gate | Result |
| --- | --- |
| Owner AC disconnect/reconnect regression check | PASS; no abnormal Energy Signals value and unknown rate displayed as `Unavailable` |
| Windows directory package rebuild | PASS with PyInstaller 6.22.2 |
| Explicit-mock packaged HTTP/shutdown smoke | PASS; `/health`, `/snapshot`, `/`, and clean exit |
| ZIP checksum, extraction, and required layout | PASS |
| Native packaged two-run full flow | PASS |
| Python suite | `63 passed` |
| Dashboard suite | `27 passed` across 4 files |
| Windows CTest | `1/1` passed |
| Scoped diff whitespace check | `git diff --check` PASS |

Together with the owner-run 9B-9D results, this proves the planned packaged Windows flow: collect,
estimate with nullable fallback, persist, query, stream, display in the Dashboard and Overlay, shut
down, and restart. Live Linux collection and GPU vendor adapters remain outside the Phase 9 gate.
