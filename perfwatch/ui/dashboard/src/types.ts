export interface CpuMetrics {
  usage_percent: number;
  frequency_mhz: number;
  package_power_watts: number;
  temperature_celsius: number;
}

export interface MemoryMetrics {
  total_bytes: number;
  used_bytes: number;
}

export interface BatteryMetrics {
  available: boolean;
  charging: boolean;
  percent: number;
  power_watts: number;
  energy_remaining_wh: number;
}

export interface GpuMetrics {
  available: boolean;
  vendor: string;
  usage_percent: number;
  vram_total_bytes: number;
  vram_used_bytes: number;
  power_watts: number;
  temperature_celsius: number;
}

export interface ProcessSample {
  timestamp_ms?: number;
  pid: number;
  name: string;
  cpu_percent: number;
  rss_bytes: number;
  vram_bytes: number;
  estimated_power_score: number;
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
  cpu_percent: number;
  memory_percent: number;
  cpu_power_watts: number;
  battery_percent: number;
  battery_power_watts: number;
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
