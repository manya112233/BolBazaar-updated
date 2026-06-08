import type { ReactNode } from 'react';
import StatusBadge from './StatusBadge';

export default function KpiCard({
  label,
  value,
  meta,
  tone = 'neutral',
  trend,
  footer,
}: {
  label: string;
  value: string;
  meta?: string;
  tone?: 'success' | 'warning' | 'danger' | 'neutral' | 'info';
  trend?: string;
  footer?: ReactNode;
}) {
  return (
    <article className={`bb-kpi-card bb-kpi-card-${tone}`}>
      <div className="bb-kpi-head">
        <span className="bb-kpi-label">{label}</span>
        {trend ? <StatusBadge label={trend} tone={tone === 'neutral' ? 'info' : tone} /> : null}
      </div>
      <strong className="bb-kpi-value">{value}</strong>
      {meta ? <p className="bb-kpi-meta">{meta}</p> : null}
      {footer ? <div className="bb-kpi-footer">{footer}</div> : null}
    </article>
  );
}
