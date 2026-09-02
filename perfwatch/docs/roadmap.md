# Roadmap

Phases 1-9 are complete and produced the current Windows product:

1. deterministic mock and native boundaries;
2. SQLite persistence and analytics enrichment;
3. FastAPI HTTP/WebSocket service;
4. React Dashboard with history, process data, reconnect, and HTTP fallback;
5. Windows live collection and Win32 Overlay;
6. CI, packaged runtime, ZIP/checksum release path, and physical Windows acceptance.

Current maintenance should focus on correctness and usability of this delivered path. Linux
collection, vendor GPU adapters, signing, installers, or update services are not planned work; each
requires a concrete requirement and a suitable validation environment before implementation.
