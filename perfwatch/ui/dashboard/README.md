# PerfWatch Dashboard

The React/Vite Dashboard displays current and historical local telemetry, top processes, connection
state, and unavailable/estimated values.

From this directory:

```powershell
npm.cmd install
npm.cmd run dev
npm.cmd test
npm.cmd run build
```

The development server proxies `/api` and `/ws` to `127.0.0.1:8000`. Production uses same-origin
paths and is served by the packaged Python runtime. Complete setup and release instructions are in
the project [README](../../README.md).
