interface MetricCardProps {
  label: string;
  value: string;
  detail: string;
  tone?: "cyan" | "amber" | "violet" | "green";
}

export function MetricCard({
  label,
  value,
  detail,
  tone = "cyan",
}: MetricCardProps) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <p className="metric-card__label">{label}</p>
      <strong className="metric-card__value">{value}</strong>
      <p className="metric-card__detail">{detail}</p>
    </article>
  );
}
