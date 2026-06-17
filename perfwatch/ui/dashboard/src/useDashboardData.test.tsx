import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useDashboardData } from "./useDashboardData";
import { snapshotFixture } from "./test/fixtures";
import type { Snapshot } from "./types";

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSED = 3;

  readonly url: string;
  readyState: number = MockWebSocket.CONNECTING;
  closeCalls = 0;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(url: string | URL) {
    this.url = String(url);
    MockWebSocket.instances.push(this);
  }

  close(): void {
    this.closeCalls += 1;
    this.readyState = MockWebSocket.CLOSED;
  }

  serverOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.(new Event("open"));
  }

  serverMessage(snapshot: Snapshot): void {
    this.onmessage?.(
      new MessageEvent("message", { data: JSON.stringify(snapshot) }),
    );
  }

  serverClose(): void {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent("close"));
  }
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((promiseResolve) => {
    resolve = promiseResolve;
  });
  return { promise, resolve };
}

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function installSuccessfulFetch(): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);

    if (url.endsWith("/health")) {
      return response({ status: "ok" });
    }
    if (url.includes("/metrics/recent")) {
      return response([snapshotFixture]);
    }
    if (url.includes("/processes/top")) {
      return response(snapshotFixture.top_processes);
    }
    if (url.endsWith("/snapshot")) {
      return response(snapshotFixture);
    }
    return response({ detail: "not found" }, 404);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("useDashboardData", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("loads HTTP data and applies live WebSocket snapshots", async () => {
    const fetchMock = installSuccessfulFetch();
    const { result } = renderHook(() => useDashboardData());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(result.current.apiHealthy).toBe(true);
    expect(result.current.snapshot?.cpu.usage_percent).toBe(42.5);
    expect(result.current.processes[0].name).toBe("mock_process");
    expect(result.current.metrics).toHaveLength(1);

    const socket = MockWebSocket.instances[0];
    act(() => socket.serverOpen());
    expect(result.current.connectionMode).toBe("live");

    const liveSnapshot: Snapshot = {
      ...snapshotFixture,
      timestamp_ms: snapshotFixture.timestamp_ms + 1_000,
      cpu: { ...snapshotFixture.cpu, usage_percent: 73 },
    };
    act(() => socket.serverMessage(liveSnapshot));

    expect(result.current.snapshot?.cpu.usage_percent).toBe(73);
    expect(result.current.metrics).toHaveLength(2);
  });

  it("reconnects after one second and polls HTTP while disconnected", async () => {
    vi.useFakeTimers();
    const fetchMock = installSuccessfulFetch();
    const { result } = renderHook(() => useDashboardData());

    await act(async () => {
      await vi.runAllTicks();
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.loading).toBe(false);

    act(() => MockWebSocket.instances[0].serverClose());
    expect(result.current.connectionMode).toBe("reconnecting");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1_000);
    });
    expect(MockWebSocket.instances).toHaveLength(2);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(4_000);
    });
    expect(fetchMock.mock.calls.length).toBeGreaterThan(4);
    expect(result.current.connectionMode).toBe("fallback");
  });

  it("uses the complete bounded reconnect schedule", async () => {
    vi.useFakeTimers();
    installSuccessfulFetch();
    const { result, unmount } = renderHook(() => useDashboardData());

    await act(async () => {
      await vi.runAllTicks();
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.loading).toBe(false);

    const delays = [1_000, 2_000, 4_000, 8_000, 10_000, 10_000];
    for (const delay of delays) {
      const socketCount = MockWebSocket.instances.length;
      act(() => MockWebSocket.instances.at(-1)?.serverClose());

      await act(async () => {
        await vi.advanceTimersByTimeAsync(delay - 1);
      });
      expect(MockWebSocket.instances).toHaveLength(socketCount);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1);
      });
      expect(MockWebSocket.instances).toHaveLength(socketCount + 1);
    }

    unmount();
  });

  it("resets reconnect delay after a WebSocket opens", async () => {
    vi.useFakeTimers();
    installSuccessfulFetch();
    const { result, unmount } = renderHook(() => useDashboardData());

    await act(async () => {
      await vi.runAllTicks();
      await vi.advanceTimersByTimeAsync(0);
    });
    act(() => MockWebSocket.instances[0].serverClose());
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1_000);
    });

    const reconnectedSocket = MockWebSocket.instances[1];
    act(() => reconnectedSocket.serverOpen());
    expect(result.current.connectionMode).toBe("live");
    act(() => reconnectedSocket.serverClose());

    await act(async () => {
      await vi.advanceTimersByTimeAsync(999);
    });
    expect(MockWebSocket.instances).toHaveLength(2);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(MockWebSocket.instances).toHaveLength(3);

    unmount();
  });

  it("does not let a late fallback response overwrite live data", async () => {
    vi.useFakeTimers();
    const fallbackSnapshot = deferred<Response>();
    let snapshotCalls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/health")) {
          return response({ status: "ok" });
        }
        if (url.includes("/metrics/recent")) {
          return response([snapshotFixture]);
        }
        if (url.includes("/processes/top")) {
          return response(snapshotFixture.top_processes);
        }
        if (url.endsWith("/snapshot")) {
          snapshotCalls += 1;
          return snapshotCalls === 1
            ? response(snapshotFixture)
            : fallbackSnapshot.promise;
        }
        return response({}, 404);
      }),
    );

    const { result, unmount } = renderHook(() => useDashboardData());
    await act(async () => {
      await vi.runAllTicks();
      await vi.advanceTimersByTimeAsync(0);
    });

    act(() => MockWebSocket.instances[0].serverClose());
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1_000);
    });
    act(() => MockWebSocket.instances[1].serverOpen());

    const liveSnapshot: Snapshot = {
      ...snapshotFixture,
      timestamp_ms: snapshotFixture.timestamp_ms + 2_000,
      cpu: { ...snapshotFixture.cpu, usage_percent: 88 },
    };
    act(() => MockWebSocket.instances[1].serverMessage(liveSnapshot));

    const staleSnapshot: Snapshot = {
      ...snapshotFixture,
      timestamp_ms: snapshotFixture.timestamp_ms + 1_000,
      cpu: { ...snapshotFixture.cpu, usage_percent: 5 },
    };
    await act(async () => {
      fallbackSnapshot.resolve(response(staleSnapshot));
      await vi.runAllTicks();
    });

    expect(result.current.connectionMode).toBe("live");
    expect(result.current.snapshot?.cpu.usage_percent).toBe(88);
    unmount();
  });

  it("falls back and retries when WebSocket construction throws", async () => {
    vi.useFakeTimers();
    installSuccessfulFetch();

    class ThrowingWebSocket {
      static attempts = 0;

      constructor() {
        ThrowingWebSocket.attempts += 1;
        throw new Error("invalid WebSocket URL");
      }
    }

    vi.stubGlobal("WebSocket", ThrowingWebSocket);
    const { result, unmount } = renderHook(() => useDashboardData());

    await act(async () => {
      await vi.runAllTicks();
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.connectionMode).toBe("fallback");
    expect(ThrowingWebSocket.attempts).toBe(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1_000);
    });
    expect(ThrowingWebSocket.attempts).toBe(2);
    unmount();
  });

  it("cleans up reconnect and polling work on unmount", async () => {
    vi.useFakeTimers();
    const fetchMock = installSuccessfulFetch();
    const { result, unmount } = renderHook(() => useDashboardData());

    await act(async () => {
      await vi.runAllTicks();
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.loading).toBe(false);

    act(() => MockWebSocket.instances[0].serverClose());
    const socketCount = MockWebSocket.instances.length;
    const fetchCount = fetchMock.mock.calls.length;
    unmount();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(20_000);
    });
    expect(MockWebSocket.instances).toHaveLength(socketCount);
    expect(fetchMock).toHaveBeenCalledTimes(fetchCount);
  });

  it("closes an active WebSocket on unmount", async () => {
    installSuccessfulFetch();
    const { result, unmount } = renderHook(() => useDashboardData());

    await waitFor(() => expect(result.current.loading).toBe(false));
    const socket = MockWebSocket.instances[0];
    unmount();

    expect(socket.closeCalls).toBe(1);
  });

  it("exposes a fatal error when the initial snapshot is unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/snapshot")) {
          return response({ detail: "snapshot unavailable" }, 503);
        }
        if (url.endsWith("/health")) {
          return response({ status: "ok" });
        }
        return response([]);
      }),
    );

    const { result } = renderHook(() => useDashboardData());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe("Current snapshot is unavailable.");
    expect(result.current.snapshot).toBeNull();
    expect(result.current.connectionMode).toBe("disconnected");
  });
});
