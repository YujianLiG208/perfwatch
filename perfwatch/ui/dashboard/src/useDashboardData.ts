import { useEffect, useState } from "react";

import {
  fetchHealth,
  fetchRecentMetrics,
  fetchSnapshot,
  fetchTopProcesses,
} from "./api";
import { getReconnectDelay, resolveWebSocketUrl } from "./connection";
import { appendMetricSample, snapshotToMetricSample } from "./data";
import type {
  ConnectionMode,
  MetricSample,
  ProcessSample,
  Snapshot,
} from "./types";

const FALLBACK_POLL_INTERVAL_MS = 5_000;
const WEBSOCKET_URL = import.meta.env.VITE_WS_URL ?? "/ws/snapshot";

export interface DashboardData {
  loading: boolean;
  error: string | null;
  notice: string | null;
  apiHealthy: boolean;
  connectionMode: ConnectionMode;
  snapshot: Snapshot | null;
  metrics: MetricSample[];
  processes: ProcessSample[];
  lastUpdated: number | null;
}

export function useDashboardData(): DashboardData {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [apiHealthy, setApiHealthy] = useState(false);
  const [connectionMode, setConnectionMode] =
    useState<ConnectionMode>("connecting");
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [metrics, setMetrics] = useState<MetricSample[]>([]);
  const [processes, setProcesses] = useState<ProcessSample[]>([]);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  useEffect(() => {
    const abortController = new AbortController();
    let disposed = false;
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let pollingTimer: ReturnType<typeof setInterval> | null = null;
    let activePollController: AbortController | null = null;
    let reconnectAttempt = 0;
    let pollGeneration = 0;
    let pollInFlight = false;
    let websocketLive = false;

    const applySnapshot = (nextSnapshot: Snapshot): void => {
      if (disposed) {
        return;
      }
      setSnapshot(nextSnapshot);
      setProcesses(nextSnapshot.top_processes.slice(0, 10));
      setMetrics((currentMetrics) =>
        appendMetricSample(
          currentMetrics,
          snapshotToMetricSample(nextSnapshot),
        ),
      );
      setLastUpdated(nextSnapshot.timestamp_ms);
      setError(null);
    };

    const stopPolling = (): void => {
      pollGeneration += 1;
      if (pollingTimer !== null) {
        clearInterval(pollingTimer);
        pollingTimer = null;
      }
      activePollController?.abort();
      activePollController = null;
      pollInFlight = false;
    };

    const pollHttp = async (generation: number): Promise<void> => {
      if (
        disposed ||
        websocketLive ||
        generation !== pollGeneration ||
        pollInFlight
      ) {
        return;
      }

      const pollController = new AbortController();
      activePollController = pollController;
      pollInFlight = true;
      const [healthResult, snapshotResult, processResult] =
        await Promise.allSettled([
          fetchHealth(pollController.signal),
          fetchSnapshot(pollController.signal),
          fetchTopProcesses(pollController.signal),
        ]);

      if (
        disposed ||
        websocketLive ||
        generation !== pollGeneration
      ) {
        if (activePollController === pollController) {
          activePollController = null;
          pollInFlight = false;
        }
        return;
      }

      setApiHealthy(
        healthResult.status === "fulfilled" &&
          healthResult.value.status === "ok",
      );

      if (snapshotResult.status === "fulfilled") {
        applySnapshot(snapshotResult.value);
        if (processResult.status === "fulfilled") {
          setProcesses(processResult.value.slice(0, 10));
        }
        setConnectionMode("fallback");
      } else {
        setConnectionMode("disconnected");
      }

      if (activePollController === pollController) {
        activePollController = null;
        pollInFlight = false;
      }
    };

    const startPolling = (): void => {
      if (pollingTimer !== null) {
        return;
      }
      pollGeneration += 1;
      const generation = pollGeneration;
      void pollHttp(generation);
      pollingTimer = setInterval(() => {
        void pollHttp(generation);
      }, FALLBACK_POLL_INTERVAL_MS);
    };

    function handleWebSocketDisconnect(): void {
      if (disposed) {
        return;
      }

      websocketLive = false;
      setConnectionMode("reconnecting");
      startPolling();

      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
      }
      const delay = getReconnectDelay(reconnectAttempt);
      reconnectAttempt += 1;
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connectWebSocket(true);
      }, delay);
    }

    function connectWebSocket(isReconnect: boolean): void {
      if (disposed) {
        return;
      }

      setConnectionMode(isReconnect ? "reconnecting" : "connecting");
      let nextSocket: WebSocket;
      try {
        nextSocket = new WebSocket(resolveWebSocketUrl(WEBSOCKET_URL));
      } catch {
        socket = null;
        handleWebSocketDisconnect();
        return;
      }
      socket = nextSocket;

      nextSocket.onopen = () => {
        if (disposed || socket !== nextSocket) {
          return;
        }
        websocketLive = true;
        reconnectAttempt = 0;
        stopPolling();
        setConnectionMode("live");
      };

      nextSocket.onmessage = (event) => {
        if (disposed || socket !== nextSocket) {
          return;
        }
        try {
          applySnapshot(JSON.parse(event.data) as Snapshot);
        } catch {
          setNotice("A live update could not be read.");
        }
      };

      nextSocket.onclose = () => {
        if (disposed || socket !== nextSocket) {
          return;
        }
        socket = null;
        handleWebSocketDisconnect();
      };
    }

    const initialize = async (): Promise<void> => {
      const [healthResult, snapshotResult, historyResult, processResult] =
        await Promise.allSettled([
          fetchHealth(abortController.signal),
          fetchSnapshot(abortController.signal),
          fetchRecentMetrics(abortController.signal),
          fetchTopProcesses(abortController.signal),
        ]);

      if (disposed) {
        return;
      }

      setApiHealthy(
        healthResult.status === "fulfilled" &&
          healthResult.value.status === "ok",
      );

      if (snapshotResult.status === "rejected") {
        setLoading(false);
        setError("Current snapshot is unavailable.");
        setConnectionMode("disconnected");
        return;
      }

      const initialSnapshot = snapshotResult.value;
      const initialMetrics =
        historyResult.status === "fulfilled"
          ? historyResult.value.reduce<MetricSample[]>(
              (currentMetrics, metricSnapshot) =>
                appendMetricSample(
                  currentMetrics,
                  snapshotToMetricSample(metricSnapshot),
                ),
              [],
            )
          : [];

      setSnapshot(initialSnapshot);
      setMetrics(
        appendMetricSample(
          initialMetrics,
          snapshotToMetricSample(initialSnapshot),
        ),
      );
      setProcesses(
        processResult.status === "fulfilled"
          ? processResult.value.slice(0, 10)
          : initialSnapshot.top_processes.slice(0, 10),
      );
      setLastUpdated(initialSnapshot.timestamp_ms);

      if (
        historyResult.status === "rejected" ||
        processResult.status === "rejected"
      ) {
        setNotice("Some historical or process data is temporarily unavailable.");
      }

      setLoading(false);
      connectWebSocket(false);
    };

    void initialize();

    return () => {
      disposed = true;
      abortController.abort();
      stopPolling();
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
      }
      socket?.close();
    };
  }, []);

  return {
    loading,
    error,
    notice,
    apiHealthy,
    connectionMode,
    snapshot,
    metrics,
    processes,
    lastUpdated,
  };
}
