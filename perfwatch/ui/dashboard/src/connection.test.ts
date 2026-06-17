import { describe, expect, it } from "vitest";

import { getReconnectDelay, resolveWebSocketUrl } from "./connection";

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

  it("caps reconnect delay at ten seconds", () => {
    expect([0, 1, 2, 3, 4, 5, 20].map(getReconnectDelay)).toEqual([
      1_000, 2_000, 4_000, 8_000, 10_000, 10_000, 10_000,
    ]);
  });
});
