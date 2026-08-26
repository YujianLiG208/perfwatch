import { describe, expect, it } from "vitest";

import {
  appendMetricSample,
  formatBytes,
  formatDurationSeconds,
  formatMetric,
  formatPercent,
  snapshotToMetricSample,
} from "./data";
import { snapshotFixture } from "./test/fixtures";

describe("snapshot data mapping", () => {
  it("maps backend snapshot fields to chart values", () => {
    expect(snapshotToMetricSample(snapshotFixture)).toEqual({
      timestamp_ms: 1_710_000_000_000,
      cpu_percent: 42.5,
      memory_percent: 50,
      cpu_power_watts: 35,
      battery_percent: 78,
      battery_power_watts: 18.5,
    });
  });

  it("sorts, de-duplicates, and caps chart samples at 60", () => {
    const samples = Array.from({ length: 60 }, (_, index) => ({
      ...snapshotToMetricSample(snapshotFixture),
      timestamp_ms: index + 2,
    }));
    const duplicate = {
      ...snapshotToMetricSample(snapshotFixture),
      timestamp_ms: 20,
      cpu_percent: 99,
    };

    const result = appendMetricSample(samples, duplicate);

    expect(result).toHaveLength(60);
    expect(result[0].timestamp_ms).toBe(2);
    expect(result.find((sample) => sample.timestamp_ms === 20)?.cpu_percent).toBe(99);
    expect(result.at(-1)?.timestamp_ms).toBe(61);
  });
});

describe("metric formatting", () => {
  it("formats percentages and binary byte values", () => {
    expect(formatPercent(42.54)).toBe("42.5%");
    expect(formatPercent(null)).toBe("Unavailable");
    expect(formatBytes(268_435_456)).toBe("256 MB");
    expect(formatBytes(0)).toBe("0 B");
    expect(formatBytes(null)).toBe("Unavailable");
    expect(formatMetric(null, "W")).toBe("Unavailable");
  });

  it.each([
    [null, "Unavailable"],
    [-1, "Unavailable"],
    [59, "1m"],
    [3_600, "1h 0m"],
    [8_756.756, "2h 26m"],
  ])("formats duration %s as %s", (value, expected) => {
    expect(formatDurationSeconds(value)).toBe(expected);
  });
});
