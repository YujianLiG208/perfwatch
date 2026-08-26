export interface CpuMetrics {
  usage_percent: number | null;
  frequency_mhz: number | null;
  package_power_watts: number | null;
  temperature_celsius: number | null;
}

export interface MemoryMetrics {
  total_bytes: number | null;
  used_bytes: number | null;
}

export interface BatteryMetrics {
  available: boolean;
  charging: boolean | null;
  percent: number | null;
  power_watts: number | null;
  energy_remaining_wh: number | null;
  estimated_remaining_seconds: number | null;
}

export interface GpuMetrics {
  available: boolean;
  vendor: string;
  usage_percent: number | null;
  vram_total_bytes: number | null;
  vram_used_bytes: number | null;
  power_watts: number | null;
  temperature_celsius: number | null;
}

export interface ProcessSample {
  timestamp_ms?: number;
  pid: number;
  name: string;
  cpu_percent: number | null;
  rss_bytes: number | null;
  vram_bytes: number | null;
  estimated_power_score: number | null;
}

export interface Snapshot {
  timestamp_ms: number;
  cpu: CpuMetrics;
  memory: MemoryMetrics;
  battery: BatteryMetrics;
  gpu: GpuMetrics;
  top_processes: ProcessSample[];
}

export interface MetricSample {
  timestamp_ms: number;
  cpu_percent: number | null;
  memory_percent: number | null;
  cpu_power_watts: number | null;
  battery_percent: number | null;
  battery_power_watts: number | null;
}

export interface HealthResponse {
  status: string;
}

export type ConnectionMode =
  | "connecting"
  | "live"
  | "fallback"
  | "reconnecting"
  | "disconnected";
