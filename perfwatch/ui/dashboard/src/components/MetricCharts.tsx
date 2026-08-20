import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MetricSample } from "../types";

interface MetricChartsProps {
  metrics: MetricSample[];
}

function formatTime(timestamp: number): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(timestamp);
}

function ChartEmptyState() {
  return (
    <div className="chart-empty">
      Historical samples will appear after the first update.
    </div>
  );
}

export function MetricCharts({ metrics }: MetricChartsProps) {
  return (
    <section className="chart-grid" aria-label="Metric history">
      <article className="panel chart-panel">
        <div className="panel__heading">
          <div>
            <p className="eyebrow">System load</p>
            <h2>CPU and memory</h2>
          </div>
          <span className="panel__unit">percent</span>
        </div>
        {metrics.length === 0 ? (
          <ChartEmptyState />
        ) : (
          <div className="chart-frame">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics}>
                <CartesianGrid stroke="#1d3049" strokeDasharray="4 6" />
                <XAxis
                  dataKey="timestamp_ms"
                  stroke="#6f829d"
                  tickFormatter={formatTime}
                  minTickGap={30}
                />
                <YAxis stroke="#6f829d" domain={[0, 100]} width={36} />
                <Tooltip
                  labelFormatter={(value) => formatTime(Number(value))}
                  contentStyle={{
                    background: "#0d1928",
                    border: "1px solid #29415f",
                    borderRadius: 10,
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="cpu_percent"
                  name="CPU %"
                  stroke="#42d9ff"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="memory_percent"
                  name="Memory %"
                  stroke="#8b7cff"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </article>

      <article className="panel chart-panel">
        <div className="panel__heading">
          <div>
            <p className="eyebrow">Energy signals</p>
            <h2>Power and battery</h2>
          </div>
          <span className="panel__unit">watts / percent</span>
        </div>
        {metrics.length === 0 ? (
          <ChartEmptyState />
        ) : (
          <div className="chart-frame">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics}>
                <CartesianGrid stroke="#1d3049" strokeDasharray="4 6" />
                <XAxis
                  dataKey="timestamp_ms"
                  stroke="#6f829d"
                  tickFormatter={formatTime}
                  minTickGap={30}
                />
                <YAxis yAxisId="watts" stroke="#6f829d" width={36} />
                <YAxis
                  yAxisId="percent"
                  orientation="right"
                  stroke="#6f829d"
                  domain={[0, 100]}
                  width={36}
                />
                <Tooltip
                  labelFormatter={(value) => formatTime(Number(value))}
                  contentStyle={{
                    background: "#0d1928",
                    border: "1px solid #29415f",
                    borderRadius: 10,
                  }}
                />
                <Line
                  yAxisId="watts"
                  type="monotone"
                  dataKey="cpu_power_watts"
                  name="CPU package W"
                  stroke="#ffbd5b"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  yAxisId="watts"
                  type="monotone"
                  dataKey="battery_power_watts"
                  name="Battery W"
                  stroke="#5ce1a8"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  yAxisId="percent"
                  type="monotone"
                  dataKey="battery_percent"
                  name="Battery %"
                  stroke="#f277c6"
                  strokeWidth={2}
                  strokeDasharray="6 5"
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </article>
    </section>
  );
}
