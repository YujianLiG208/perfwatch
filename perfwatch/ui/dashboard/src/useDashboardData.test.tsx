import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useDashboardData } from "./useDashboardData";
import { snapshotFixture } from "./test/fixtures";
import type { Snapshot } from "./types";

class MockWebSocket extends EventTarget {
  static instances: MockWebSocket[] = [];
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSED = 3;

  readonly url: string;
  readyState: number = MockWebSocket.CONNECTING;
  closeCalls = 0;
  constructor(url: string | URL) {
    super();
    this.url = String(url);
    MockWebSocket.instances.push(this);
  }

  close(): void {
    this.closeCalls += 1;
    this.readyState = MockWebSocket.CLOSED;
  }

  serverOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    this.dispatchEvent(new Event("open"));
  }

  serverMessage(snapshot: Snapshot): void {
    this.dispatchEvent(
      new MessageEvent("message", { data: JSON.stringify(snapshot) }),
    );
  }

  serverClose(): void {
    this.readyState = MockWebSocket.CLOSED;
    this.dispatchEvent(new CloseEvent("close"));
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
    const { result, unmount } = renderHook(() => useDashboardData());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(result.current.apiHealthy).toBe(true);
    expect(result.current.snapshot?.cpu.usage_percent).toBe(42.5);
    expect(result.current.processes[0].name).toBe("mock_process");
    expect(result.current.metrics).toHaveLength(1);

    await waitFor(() => expect(MockWebSocket.instances).toHaveLength(1));
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
    unmount();
    expect(socket.closeCalls).toBe(1);
  });

  it("backs off retries, resets on open, and polls HTTP while disconnected", async () => {
    vi.useFakeTimers();
    const fetchMock = installSuccessfulFetch();
    const { result } = renderHook(() => useDashboardData());

    await act(async () => {
      await vi.runAllTicks();
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.loading).toBe(false);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    act(() => MockWebSocket.instances[0].serverClose());
    expect(result.current.connectionMode).toBe("reconnecting");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1_000);
    });
    expect(MockWebSocket.instances).toHaveLength(2);

    act(() => MockWebSocket.instances[1].serverClose());
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });
    expect(MockWebSocket.instances).toHaveLength(3);

    await act(async () => {
      // Include the query's deferred notification after the five-second poll.
      await vi.advanceTimersByTimeAsync(2_001);
    });
    expect(fetchMock).toHaveBeenCalledTimes(10);
    expect(result.current.connectionMode).toBe("fallback");

    act(() => MockWebSocket.instances[2].serverOpen());
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    act(() => MockWebSocket.instances[2].serverClose());
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1_000);
    });
    expect(MockWebSocket.instances).toHaveLength(4);
  });

  it("does not let a late fallback response overwrite live data", async () => {
    vi.useFakeTimers();
    const fallbackSnapshot = deferred<Response>();
    const fallbackSignals: AbortSignal[] = [];
    let snapshotCalls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
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
          if (snapshotCalls > 1 && init?.signal) {
            fallbackSignals.push(init.signal);
          }
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
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    act(() => MockWebSocket.instances[0].serverClose());
    await act(async () => {
      // Let one handshake time out while the HTTP fallback remains in flight.
      await vi.advanceTimersByTimeAsync(7_001);
    });
    expect(snapshotCalls).toBe(2);
    expect(fallbackSignals[0].aborted).toBe(false);
    const socket = MockWebSocket.instances.at(-1)!;
    expect(socket.readyState).toBe(MockWebSocket.CONNECTING);
    act(() => socket.serverOpen());
    expect(fallbackSignals[0].aborted).toBe(true);

    const liveSnapshot: Snapshot = {
      ...snapshotFixture,
      timestamp_ms: snapshotFixture.timestamp_ms + 2_000,
      cpu: { ...snapshotFixture.cpu, usage_percent: 88 },
    };
    act(() => socket.serverMessage(liveSnapshot));

    const staleSnapshot: Snapshot = {
      ...snapshotFixture,
      timestamp_ms: snapshotFixture.timestamp_ms + 1_000,
      cpu: { ...snapshotFixture.cpu, usage_percent: 5 },
    };
    act(() => MockWebSocket.instances[0].serverMessage(staleSnapshot));
    await act(async () => {
      fallbackSnapshot.resolve(response(staleSnapshot));
      await vi.advanceTimersByTimeAsync(5_000);
    });

    expect(snapshotCalls).toBe(2);
    expect(result.current.connectionMode).toBe("live");
    expect(result.current.snapshot?.cpu.usage_percent).toBe(88);
    unmount();
  });

  it("handles constructor failure and stops reconnect and polling on unmount", async () => {
    vi.useFakeTimers();
    const fetchMock = installSuccessfulFetch();
    const createSocket = vi.fn(function (url: string | URL) {
      if (createSocket.mock.calls.length === 1) {
        throw new Error("WebSocket construction failed");
      }
      return new MockWebSocket(url);
    });
    vi.stubGlobal("WebSocket", createSocket);
    const { result, unmount } = renderHook(() => useDashboardData());

    await act(async () => {
      await vi.runAllTicks();
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.loading).toBe(false);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.connectionMode).toBe("reconnecting");
    expect(fetchMock).toHaveBeenCalledTimes(7);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1_000);
    });
    expect(createSocket).toHaveBeenCalledTimes(2);

    act(() => MockWebSocket.instances[0].serverClose());
    const fetchCount = fetchMock.mock.calls.length;
    unmount();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(20_000);
    });
    expect(createSocket).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenCalledTimes(fetchCount);
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
