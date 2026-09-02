# Scope

PerfWatch is a local Windows performance and energy monitor. The completed product includes:

- live Windows CPU, memory, battery, and process collection;
- estimated battery runtime and relative process energy scores;
- SQLite persistence, HTTP/WebSocket APIs, and a React Dashboard;
- a native click-through Win32 Overlay;
- an unsigned Windows x64 directory bundle, ZIP, checksum, and tag-gated release workflow.

Unsupported measurements remain unavailable instead of becoming zero or mock data. Mock collection
is explicit and intended for tests and package smoke checks.

Linux collection, vendor-specific GPU collection, installers, signing, automatic updates, cloud
services, and remote telemetry are outside the current product. Add them only when a concrete user
requirement and validation environment exist.
