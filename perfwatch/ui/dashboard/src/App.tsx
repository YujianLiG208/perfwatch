import { MetricCharts } from "./components/MetricCharts";
import { MetricCard } from "./components/MetricCard";
import { ProcessTable } from "./components/ProcessTable";
import { StatusBar } from "./components/StatusBar";
import {
  formatBytes,
  formatDurationSeconds,
  formatMetric,
  formatPercent,
} from "./data";
import { useDashboardData } from "./useDashboardData";
import "./styles.css";

function App() {
  const {
    loading,
    error,
    notice,
    apiHealthy,
    connectionMode,
    snapshot,
    metrics,
    processes,
    lastUpdated,
  } = useDashboardData();

  if (loading) {
    return (
      <main className="app-shell app-shell--centered">
        <div className="loading-state" role="status">
          <span className="loading-state__pulse" />
          <p>Loading current snapshot...</p>
        </div>
      </main>
    );
  }

  if (error !== null && snapshot === null) {
    return (
      <main className="app-shell app-shell--centered">
        <section className="fatal-state" role="alert">
          <p className="eyebrow">Connection error</p>
          <h1>Dashboard unavailable</h1>
          <p>{error}</p>
          <span>Start the local perfwatch API and refresh this page.</span>
        </section>
      </main>
    );
  }

  if (snapshot === null) {
    return null;
  }

  const memoryPercent =
    snapshot.memory.total_bytes !== null &&
    snapshot.memory.used_bytes !== null &&
    snapshot.memory.total_bytes > 0
      ? (snapshot.memory.used_bytes / snapshot.memory.total_bytes) * 100
      : null;
  const highestProcess = processes[0];

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Local system telemetry</p>
          <h1>
            perf<span>watch</span>
          </h1>
          <p className="app-header__subtitle">
            Performance and energy signals, sampled on this machine.
          </p>
        </div>
        <StatusBar
          apiHealthy={apiHealthy}
          connectionMode={connectionMode}
          lastUpdated={lastUpdated}
        />
      </header>

      {notice !== null && (
        <div className="notice" role="status">
          {notice}
        </div>
      )}

      <section className="metric-grid" aria-label="Current metrics">
        <MetricCard
          label="CPU usage"
          value={formatPercent(snapshot.cpu.usage_percent)}
          detail={`${formatMetric(snapshot.cpu.frequency_mhz, "GHz", 2, 1_000)} / ${formatMetric(snapshot.cpu.temperature_celsius, "C")}`}
        />
        <MetricCard
          label="Memory used"
          value={formatPercent(memoryPercent)}
          detail={`${formatBytes(snapshot.memory.used_bytes)} of ${formatBytes(snapshot.memory.total_bytes)}`}
          tone="violet"
        />
        <MetricCard
          label="Battery"
          value={
            snapshot.battery.available
              ? formatPercent(snapshot.battery.percent)
              : "Not available"
          }
          detail={
            !snapshot.battery.available
              ? "No battery sample reported"
              : snapshot.battery.charging === true
                ? "Charging"
                : snapshot.battery.charging === false &&
                    snapshot.battery.estimated_remaining_seconds !== null
                  ? `Estimated ${formatDurationSeconds(snapshot.battery.estimated_remaining_seconds)} remaining`
                  : snapshot.battery.charging === false
                    ? "Estimated time unavailable"
                    : "Status unavailable"
          }
          tone="green"
        />
        <MetricCard
          label="CPU package power"
          value={formatMetric(snapshot.cpu.package_power_watts, "W")}
          detail={`Battery signal ${formatMetric(snapshot.battery.power_watts, "W")}`}
          tone="amber"
        />
        <MetricCard
          label="Estimated process energy score"
          value={
            highestProcess
              ? highestProcess.estimated_power_score !== null
                ? highestProcess.estimated_power_score.toFixed(2)
                : "Unavailable"
              : "No sample"
          }
          detail={
            highestProcess
              ? `${highestProcess.name} / ${formatPercent(highestProcess.cpu_percent)} CPU`
              : "Waiting for process data"
          }
          tone="violet"
        />
      </section>

      <MetricCharts metrics={metrics} />
      <ProcessTable processes={processes} />

      <footer className="app-footer">
        Energy-related values are device-reported signals or estimates. Process
        energy scores are relative indicators, not measured watts.
      </footer>
    </main>
  );
}

export default App;
