import { formatBytes, formatPercent } from "../data";
import type { ProcessSample } from "../types";

interface ProcessTableProps {
  processes: ProcessSample[];
}

export function ProcessTable({ processes }: ProcessTableProps) {
  return (
    <section className="panel process-panel">
      <div className="panel__heading">
        <div>
          <p className="eyebrow">Current activity</p>
          <h2>Top processes</h2>
        </div>
        <span className="panel__unit">highest estimated score first</span>
      </div>

      {processes.length === 0 ? (
        <div className="empty-state">No process samples are available.</div>
      ) : (
        <div className="table-scroll">
          <table aria-label="Top processes">
            <thead>
              <tr>
                <th scope="col">Process</th>
                <th scope="col">PID</th>
                <th scope="col">CPU</th>
                <th scope="col">Memory</th>
                <th scope="col">VRAM</th>
                <th scope="col">Estimated score</th>
              </tr>
            </thead>
            <tbody>
              {processes.slice(0, 10).map((process) => (
                <tr key={`${process.pid}-${process.name}`}>
                  <td>
                    <span className="process-name">{process.name}</span>
                  </td>
                  <td className="mono">{process.pid}</td>
                  <td>{formatPercent(process.cpu_percent)}</td>
                  <td>{formatBytes(process.rss_bytes)}</td>
                  <td>{formatBytes(process.vram_bytes)}</td>
                  <td className="score">
                    {process.estimated_power_score !== null
                      ? process.estimated_power_score.toFixed(3)
                      : "Unavailable"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
