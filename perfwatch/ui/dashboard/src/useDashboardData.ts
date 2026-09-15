import { QueryClient, useQuery } from "@tanstack/react-query";
import ReconnectingWebSocket from "partysocket/ws";
import { useEffect, useRef, useState } from "react";

import {
  fetchHealth,
  fetchRecentMetrics,
  fetchSnapshot,
  fetchTopProcesses,
} from "./api";
import { resolveWebSocketUrl } from "./connection";
import { appendMetricSample, snapshotToMetricSample } from "./data";
import type {
  ConnectionMode,
  MetricSample,
  ProcessSample,
  Snapshot,
} from "./types";

const HTTP_QUERY_KEY = ["dashboard-http"];
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
  const [queryClient] = useState(() => new QueryClient());
  const [state, setState] = useState<DashboardData>({
    loading: true,
    error: null,
    notice: null,
    apiHealthy: false,
    connectionMode: "connecting",
    snapshot: null,
    metrics: [],
    processes: [],
    lastUpdated: null,
  });
  const [polling, setPolling] = useState(false);
  const websocketLive = useRef(false);
  const initial = state.loading;

  const { data } = useQuery(
    {
      queryKey: HTTP_QUERY_KEY,
      queryFn: async ({ signal }) => {
        const [health, snapshot, history, processes] = await Promise.allSettled([
          fetchHealth(signal),
          fetchSnapshot(signal),
          initial ? fetchRecentMetrics(signal) : Promise.resolve<Snapshot[]>([]),
          fetchTopProcesses(signal),
        ]);
        return { initial, health, snapshot, history, processes };
      },
      enabled: initial || polling,
      refetchInterval: polling ? FALLBACK_POLL_INTERVAL_MS : false,
      refetchIntervalInBackground: true,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
      retry: false,
      networkMode: "always",
      gcTime: 0,
      structuralSharing: false,
    },
    queryClient,
  );

  useEffect(() => {
    if (!data || websocketLive.current) {
      return;
    }
    setState((current) => {
      const apiHealthy =
        data.health.status === "fulfilled" && data.health.value.status === "ok";
      if (data.snapshot.status === "rejected") {
        return {
          ...current,
          loading: false,
          apiHealthy,
          connectionMode: "disconnected",
          error: data.initial ? "Current snapshot is unavailable." : current.error,
        };
      }
      const snapshot = data.snapshot.value;
      const metrics = data.initial
        ? data.history.status === "fulfilled"
          ? data.history.value.reduce<MetricSample[]>(
              (samples, sample) =>
                appendMetricSample(samples, snapshotToMetricSample(sample)),
              [],
            )
          : []
        : current.metrics;
      return {
        loading: false,
        error: null,
        notice:
          data.initial &&
          (data.history.status === "rejected" || data.processes.status === "rejected")
            ? "Some historical or process data is temporarily unavailable."
            : current.notice,
        apiHealthy,
        connectionMode: data.initial ? "connecting" : "fallback",
        snapshot,
        metrics: appendMetricSample(metrics, snapshotToMetricSample(snapshot)),
        processes: (data.processes.status === "fulfilled"
          ? data.processes.value
          : snapshot.top_processes).slice(0, 10),
        lastUpdated: snapshot.timestamp_ms,
      };
    });
  }, [data]);

  const canConnect = !state.loading && state.snapshot !== null;
  useEffect(() => {
    if (!canConnect) {
      return;
    }
    const socket = new ReconnectingWebSocket(
      () => resolveWebSocketUrl(WEBSOCKET_URL),
      [],
      {
        minReconnectionDelay: 1_000,
        maxReconnectionDelay: 10_000,
        reconnectionDelayGrowFactor: 2,
        minUptime: 0,
        connectionTimeout: 4_000,
      },
    );

    socket.onclose = socket.onerror = () => {
      websocketLive.current = false;
      setPolling(true);
      setState((current) => ({ ...current, connectionMode: "reconnecting" }));
    };
    socket.onopen = () => {
      websocketLive.current = true;
      setPolling(false);
      void queryClient.cancelQueries({ queryKey: HTTP_QUERY_KEY });
      setState((current) => ({ ...current, connectionMode: "live" }));
    };
    socket.onmessage = (event) => {
      try {
        const snapshot = JSON.parse(event.data) as Snapshot;
        const processes = snapshot.top_processes.slice(0, 10);
        const sample = snapshotToMetricSample(snapshot);
        setState((current) => ({
          ...current,
          snapshot,
          processes,
          metrics: appendMetricSample(current.metrics, sample),
          lastUpdated: snapshot.timestamp_ms,
          error: null,
        }));
      } catch {
        setState((current) => ({
          ...current,
          notice: "A live update could not be read.",
        }));
      }
    };

    return () => {
      websocketLive.current = false;
      socket.onopen = socket.onmessage = socket.onclose = socket.onerror = null;
      socket.close();
    };
  }, [canConnect, queryClient]);

  return state;
}
