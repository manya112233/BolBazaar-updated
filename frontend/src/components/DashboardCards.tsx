import StatusBadge from './StatusBadge';

import type { ReactNode } from 'react';

export function KpiCard({
  label,
  value,
  meta,
  trend,
  tone = 'neutral',
}: {
  label: string;
  value: string;
  meta?: string;
  trend?: string;
  tone?: 'success' | 'warning' | 'danger' | 'neutral' | 'info';
}) {
  return (
    <article className={`kpi-card kpi-card-${tone}`}>
      <div className="kpi-card-head">
        <span>{label}</span>
        {trend ? <StatusBadge label={trend} tone={tone === 'neutral' ? 'info' : tone} /> : null}
      </div>
      <strong>{value}</strong>
      {meta ? <p>{meta}</p> : null}
    </article>
  );
}

export function SectionCard({
  title,
  subtitle,
  action,
  children,
  className = '',
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`dashboard-card ${className}`.trim()}>
      <div className="dashboard-card-head">
        <div>
          <h3>{title}</h3>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {action ? <div className="dashboard-card-action">{action}</div> : null}
      </div>
      {children}
    </section>
  );
}

export function EmptyState({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" aria-hidden="true">
        BB
      </div>
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  );
}

export function LoadingPanel({ label }: { label: string }) {
  return (
    <div className="loading-panel" aria-label={label}>
      <div className="loading-line loading-line-lg" />
      <div className="loading-line" />
      <div className="loading-line" />
    </div>
  );
}
