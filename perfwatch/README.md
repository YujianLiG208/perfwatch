# perfwatch

perfwatch is a Windows local performance and energy monitoring prototype. It combines a C++
collection layer, Python orchestration and persistence, a FastAPI service, and a React dashboard.


## Implemented Architecture

- **C++:** live Windows CPU/memory/battery/process collection and pybind11 bindings.
- **Python:** explicit mock or native collection, battery-runtime and process-energy enrichment,
  SQLite storage, service orchestration, the packaged runtime, and native Win32 Overlay through
  `ctypes`.
- **API:** `GET /health`, `GET /snapshot`, `GET /metrics/recent`, `GET /processes/top`, and
  `WebSocket /ws/snapshot` in the integrated baseline.
- **Dashboard:** 
  served with same-origin HTTP and WebSocket paths in production. Nullable live measurements render
  as unavailable.
- **Windows product:** PyInstaller 6.22.2 assembles `perfwatch.exe`, the Dashboard, SQLite schema,
  native extension, into one unsigned directory bundle.

## Run Locally

Build the Dashboard and run the integrated local production application from the repository root:

```powershell
cd ui\dashboard
npm.cmd run build
cd ..\..
python -m pip install -e python
perfwatch-server --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. For a non-default build layout, pass the directory containing
`index.html` explicitly:

```powershell
perfwatch-server --dashboard-directory C:\path\to\dashboard\dist
```

For development with Vite hot reload, start the API and Dashboard separately.

Set up and start the API:

```powershell
cd python
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
$env:PERFWATCH_USE_MOCK_COLLECTOR = "true"
.\.venv\Scripts\python.exe -m uvicorn perfwatch.api.app:app --reload
```

In another terminal, start the dashboard:

```powershell
cd ui\dashboard
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173`.

## Windows Package and Releases

The Windows x64 deliverables are named `perfwatch-0.1.0-windows-x64.zip` and
`perfwatch-0.1.0-windows-x64.zip.sha256`. Compare the SHA-256 before expanding the archive, then run
`perfwatch\perfwatch.exe`. The archive is unsigned.

The release workflow builds on `windows-latest` for an exact `vMAJOR.MINOR.PATCH` tag matching the
project version. Manual dispatch builds and uploads the two files but cannot publish a GitHub
Release. Mock collection remains available only through the explicit `--mock` option.

## Validation

Run Python and C++ tests from the repository root:

```powershell
python -m pytest python/tests
cmake -S cpp -B build
cmake --build build --config Debug
ctest --test-dir build --output-on-failure -C Debug
```

Validate the dashboard from the same integrated checkout:

```powershell
cd ui\dashboard
npm.cmd run test
npm.cmd run build
```

