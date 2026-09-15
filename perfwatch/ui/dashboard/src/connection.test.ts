import { describe, expect, it } from "vitest";

import { resolveWebSocketUrl } from "./connection";

describe("connection configuration", () => {
  it("resolves a relative WebSocket path from the current page", () => {
    expect(
      resolveWebSocketUrl(
        "/ws/snapshot",
        new URL("https://monitor.example/dashboard"),
      ),
    ).toBe("wss://monitor.example/ws/snapshot");
  });

  it("preserves an explicitly configured WebSocket URL", () => {
    expect(
      resolveWebSocketUrl(
        "ws://127.0.0.1:9000/live",
        new URL("http://localhost:5173"),
      ),
    ).toBe("ws://127.0.0.1:9000/live");
  });
});
