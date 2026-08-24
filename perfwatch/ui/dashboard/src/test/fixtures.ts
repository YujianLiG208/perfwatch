import type { Snapshot } from "../types";

export const snapshotFixture: Snapshot = {
  timestamp_ms: 1_710_000_000_000,
  cpu: {
    usage_percent: 42.5,
    frequency_mhz: 3600,
    package_power_watts: 35,
    temperature_celsius: 65,
  },
  memory: {
    total_bytes: 34_359_738_368,
    used_bytes: 17_179_869_184,
  },
  battery: {
    available: true,
    charging: false,
    percent: 78,
    power_watts: 18.5,
    energy_remaining_wh: 45,
    estimated_remaining_seconds: 8756.756756756757,
  },
  gpu: {
    available: false,
    vendor: "unavailable",
    usage_percent: 0,
    vram_total_bytes: 0,
    vram_used_bytes: 0,
    power_watts: 0,
    temperature_celsius: 0,
  },
  top_processes: [
    {
      pid: 1234,
      name: "mock_process",
      cpu_percent: 12.5,
      rss_bytes: 268_435_456,
      vram_bytes: 0,
      estimated_power_score: 0.1,
    },
  ],
};
