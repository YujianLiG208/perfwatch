# perfwatch Dashboard

The Phase 5 dashboard is a local Vite, React, and TypeScript application. It displays current
perfwatch metrics, short time-series history, connection state, and the latest top processes.

## Run Locally

Start the Phase 4 API:

```powershell
cd python
..\.venv\Scripts\python.exe -m uvicorn perfwatch.api.app:app --reload
```

Start the dashboard in another terminal:

```powershell
cd ui\dashboard
npm.cmd install
npm.cmd run dev
```

On shells that do not require the Windows `npm.cmd` shim, use `npm run dev`.
Open `http://127.0.0.1:5173`.

## Configuration

- `VITE_API_BASE_URL` defaults to `/api`.
- `VITE_WS_URL` defaults to `/ws/snapshot`.

The Vite development server proxies `/api/*` to `http://127.0.0.1:8000` and removes the `/api`
prefix. It proxies `/ws/*` to the same backend with WebSocket support. Full HTTP or WebSocket URLs
can be supplied through the environment variables when the frontend is hosted separately.

## Test and Build

```powershell
npm.cmd run test
npm.cmd run build
```

Tests mock HTTP and WebSocket boundaries. They do not require a running backend or real hardware.

## MVP Limitations

- The dashboard keeps at most 60 chart samples in memory.
- WebSocket reconnect delays are capped at 10 seconds; HTTP fallback polls every 5 seconds.
- Process energy scores are relative estimates, not measured watts.
- The single-page production bundle includes Recharts and currently triggers Vite's 500 kB chunk
  advisory while remaining approximately 162 kB gzip-compressed.
