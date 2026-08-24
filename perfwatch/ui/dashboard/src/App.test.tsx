import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { snapshotFixture } from "./test/fixtures";

class PassiveWebSocket {
  static instances: PassiveWebSocket[] = [];

  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(readonly url: string | URL) {
    PassiveWebSocket.instances.push(this);
  }

  close(): void {}

  serverClose(): void {
    this.onclose?.(new CloseEvent("close"));
  }
}

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function installFetch(
  processCount = 1,
  snapshotStatus = 200,
  processScore: number | null = snapshotFixture.top_processes[0].estimated_power_score,
): ReturnType<typeof vi.fn> {
  const processes = Array.from({ length: processCount }, (_, index) => ({
    ...snapshotFixture.top_processes[0],
    pid: 1_000 + index,
    name: `process-${index}`,
    estimated_power_score: processScore === null ? null : processScore - index / 100,
  }));
  const snapshot = { ...snapshotFixture, top_processes: processes };

  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith("/health")) {
      return response({ status: "ok" });
    }
    if (url.endsWith("/snapshot")) {
      return response(
        snapshotStatus === 200 ? snapshot : { detail: "snapshot unavailable" },
        snapshotStatus,
      );
    }
    if (url.includes("/metrics/recent")) {
      return response([snapshot]);
    }
    if (url.includes("/processes/top")) {
      return response(processes);
    }
    return response({}, 404);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("App", () => {
  beforeEach(() => {
    PassiveWebSocket.instances = [];
    vi.stubGlobal("WebSocket", PassiveWebSocket);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders loading and current dashboard metrics", async () => {
    installFetch();
    render(<App />);

    expect(screen.getByText("Loading current snapshot...")).toBeInTheDocument();
    expect(await screen.findByText("process-0")).toBeInTheDocument();
    expect(screen.getByText("API healthy")).toBeInTheDocument();
    expect(screen.getByText("42.5%")).toBeInTheDocument();
    expect(screen.getByText("50.0%")).toBeInTheDocument();
    expect(screen.getByText("78.0%")).toBeInTheDocument();
    expect(screen.getByText("Estimated 2h 26m remaining")).toBeInTheDocument();
    expect(screen.getByText("0.10")).toBeInTheDocument();
    expect(screen.getByText("Estimated process energy score")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Top processes" })).toBeInTheDocument();
  });

  it("renders no more than ten top processes", async () => {
    installFetch(12);
    render(<App />);

    expect(await screen.findByText("process-9")).toBeInTheDocument();
    expect(screen.queryByText("process-10")).not.toBeInTheDocument();
  });

  it("renders an empty process state", async () => {
    installFetch(0);
    render(<App />);

    expect(
      await screen.findByText("No process samples are available."),
    ).toBeInTheDocument();
  });

  it("renders unavailable for a null process score", async () => {
    installFetch(1, 200, null);
    render(<App />);

    expect(await screen.findByText("process-0")).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable")).toHaveLength(2);
  });

  it("renders a fatal snapshot error", async () => {
    installFetch(0, 503);
    render(<App />);

    await waitFor(() =>
      expect(
        screen.getByText("Current snapshot is unavailable."),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText("Dashboard unavailable")).toBeInTheDocument();
  });

  it("renders a disconnected state when live and fallback requests fail", async () => {
    const fetchMock = installFetch();
    render(<App />);

    expect(await screen.findByText("process-0")).toBeInTheDocument();
    fetchMock.mockRejectedValue(new Error("backend unavailable"));
    act(() => PassiveWebSocket.instances[0].serverClose());

    expect(await screen.findByText("Disconnected")).toBeInTheDocument();
  });
});
