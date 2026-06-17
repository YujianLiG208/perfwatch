import type { ConnectionMode } from "../types";

const connectionLabels: Record<ConnectionMode, string> = {
  connecting: "Connecting live updates",
  live: "Live WebSocket",
  fallback: "HTTP fallback",
  reconnecting: "Reconnecting",
  disconnected: "Disconnected",
};

interface StatusBarProps {
  apiHealthy: boolean;
  connectionMode: ConnectionMode;
  lastUpdated: number | null;
}

export function StatusBar({
  apiHealthy,
  connectionMode,
  lastUpdated,
}: StatusBarProps) {
  const updatedLabel =
    lastUpdated === null
      ? "Waiting for data"
      : new Intl.DateTimeFormat(undefined, {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }).format(lastUpdated);

  return (
    <div className="status-bar" aria-label="Service status">
      <span
        className={`status-pill ${apiHealthy ? "status-pill--good" : "status-pill--bad"}`}
      >
        <span className="status-pill__dot" />
        {apiHealthy ? "API healthy" : "API unavailable"}
      </span>
      <span
        className={`status-pill status-pill--${connectionMode}`}
        data-connection={connectionMode}
      >
        <span className="status-pill__dot" />
        {connectionLabels[connectionMode]}
      </span>
      <span className="status-bar__time">Updated {updatedLabel}</span>
    </div>
  );
}
