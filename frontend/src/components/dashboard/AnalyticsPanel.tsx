import type { ReactNode } from 'react';

export type AnalyticsDatum = {
  label: string;
  value: number;
  tone?: 'green' | 'amber' | 'slate' | 'blue';
};

function toneClass(tone?: AnalyticsDatum['tone']) {
  if (tone === 'amber') return 'bb-analytics-fill-amber';
  if (tone === 'slate') return 'bb-analytics-fill-slate';
  if (tone === 'blue') return 'bb-analytics-fill-blue';
  return 'bb-analytics-fill-green';
}

export function AnalyticsCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <section className="bb-panel">
      <div className="bb-panel-head">
        <div>
          <h3>{title}</h3>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}

export function BarAnalytics({
  title,
  subtitle,
  items,
  formatValue = (value) => value.toString(),
}: {
  title: string;
  subtitle?: string;
  items: AnalyticsDatum[];
  formatValue?: (value: number) => string;
}) {
  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <AnalyticsCard title={title} subtitle={subtitle}>
      <div className="bb-analytics-list">
        {items.map((item) => (
          <div key={item.label} className="bb-analytics-row">
            <div className="bb-analytics-labels">
              <strong>{item.label}</strong>
            </div>
            <div className="bb-analytics-track">
              <div
                className={`bb-analytics-fill ${toneClass(item.tone)}`}
                style={{ width: `${Math.max((item.value / max) * 100, item.value > 0 ? 10 : 0)}%` }}
              />
            </div>
            <strong className="bb-analytics-value">{formatValue(item.value)}</strong>
          </div>
        ))}
      </div>
    </AnalyticsCard>
  );
}

export function ColumnAnalytics({
  title,
  subtitle,
  items,
  formatValue = (value) => value.toString(),
}: {
  title: string;
  subtitle?: string;
  items: AnalyticsDatum[];
  formatValue?: (value: number) => string;
}) {
  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <AnalyticsCard title={title} subtitle={subtitle}>
      <div className="bb-column-chart">
        {items.map((item) => (
          <div key={item.label} className="bb-column-chart-item">
            <span>{item.label}</span>
            <div className="bb-column-chart-shell">
              <div
                className={`bb-column-chart-bar ${toneClass(item.tone)}`}
                style={{ height: `${Math.max((item.value / max) * 100, item.value > 0 ? 10 : 0)}%` }}
              />
            </div>
            <strong>{formatValue(item.value)}</strong>
          </div>
        ))}
      </div>
    </AnalyticsCard>
  );
}
