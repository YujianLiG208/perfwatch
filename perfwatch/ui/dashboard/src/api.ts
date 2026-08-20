import type {
  HealthResponse,
  ProcessSample,
  Snapshot,
} from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "/api").replace(
  /\/$/,
  "",
);

async function requestJson<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export function fetchHealth(signal: AbortSignal): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health", signal);
}

export function fetchSnapshot(signal: AbortSignal): Promise<Snapshot> {
  return requestJson<Snapshot>("/snapshot", signal);
}

export function fetchRecentMetrics(signal: AbortSignal): Promise<Snapshot[]> {
  return requestJson<Snapshot[]>("/metrics/recent?limit=60", signal);
}

export function fetchTopProcesses(
  signal: AbortSignal,
): Promise<ProcessSample[]> {
  return requestJson<ProcessSample[]>("/processes/top?limit=10", signal);
}
