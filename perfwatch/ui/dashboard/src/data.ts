import type { MetricSample, Snapshot } from "./types";

const CHART_SAMPLE_LIMIT = 60;

export function snapshotToMetricSample(snapshot: Snapshot): MetricSample {
  const memoryPercent =
    snapshot.memory.total_bytes !== null &&
    snapshot.memory.used_bytes !== null &&
    snapshot.memory.total_bytes > 0
      ? (snapshot.memory.used_bytes / snapshot.memory.total_bytes) * 100
      : null;

  return {
    timestamp_ms: snapshot.timestamp_ms,
    cpu_percent: snapshot.cpu.usage_percent,
    memory_percent: memoryPercent,
    cpu_power_watts: snapshot.cpu.package_power_watts,
    battery_percent: snapshot.battery.percent,
    battery_power_watts: snapshot.battery.power_watts,
  };
}

export function appendMetricSample(
  samples: MetricSample[],
  sample: MetricSample,
): MetricSample[] {
  const byTimestamp = new Map(
    samples.map((currentSample) => [currentSample.timestamp_ms, currentSample]),
  );
  byTimestamp.set(sample.timestamp_ms, sample);

  return [...byTimestamp.values()]
    .sort((left, right) => left.timestamp_ms - right.timestamp_ms)
    .slice(-CHART_SAMPLE_LIMIT);
}

export function formatPercent(value: number | null): string {
  return value === null || !Number.isFinite(value)
    ? "Unavailable"
    : `${value.toFixed(1)}%`;
}

export function formatMetric(
  value: number | null,
  unit: string,
  fractionDigits = 1,
  divisor = 1,
): string {
  return value === null || !Number.isFinite(value)
    ? "Unavailable"
    : `${(value / divisor).toFixed(fractionDigits)} ${unit}`;
}

export function formatDurationSeconds(value: number | null): string {
  if (value === null || !Number.isFinite(value) || value < 0) {
    return "Unavailable";
  }
  const totalMinutes = Math.round(value / 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
}

export function formatBytes(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return "Unavailable";
  }
  if (value <= 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB", "TB"];
  const unitIndex = Math.min(
    Math.floor(Math.log(value) / Math.log(1024)),
    units.length - 1,
  );
  const scaledValue = value / 1024 ** unitIndex;
  const fractionDigits = scaledValue >= 10 || unitIndex === 0 ? 0 : 1;

  return `${scaledValue.toFixed(fractionDigits)} ${units[unitIndex]}`;
}
