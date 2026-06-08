import { SectionCard } from './DashboardCards';

type ChartDatum = {
  label: string;
  value: number;
  tone?: 'green' | 'amber' | 'slate' | 'blue';
  hint?: string;
};

const toneClass = {
  green: 'chart-tone-green',
  amber: 'chart-tone-amber',
  slate: 'chart-tone-slate',
  blue: 'chart-tone-blue',
};

export function BarListCard({
  title,
  subtitle,
  items,
  formatValue = (value) => value.toString(),
}: {
  title: string;
  subtitle?: string;
  items: ChartDatum[];
  formatValue?: (value: number) => string;
}) {
  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <SectionCard title={title} subtitle={subtitle} className="analytics-card">
      <div className="chart-list">
        {items.map((item) => (
          <div key={item.label} className="chart-row">
            <div className="chart-row-labels">
              <strong>{item.label}</strong>
              {item.hint ? <span>{item.hint}</span> : null}
            </div>
            <div className="chart-row-track">
              <div
                className={`chart-row-fill ${toneClass[item.tone || 'green']}`}
                style={{ width: `${Math.max((item.value / max) * 100, item.value > 0 ? 12 : 0)}%` }}
              />
            </div>
            <strong className="chart-row-value">{formatValue(item.value)}</strong>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

export function TimelineCard({
  title,
  subtitle,
  items,
  formatValue = (value) => value.toString(),
}: {
  title: string;
  subtitle?: string;
  items: ChartDatum[];
  formatValue?: (value: number) => string;
}) {
  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <SectionCard title={title} subtitle={subtitle} className="analytics-card">
      <div className="timeline-chart">
        {items.map((item) => (
          <div key={item.label} className="timeline-column">
            <span>{item.label}</span>
            <div className="timeline-bar-shell">
              <div
                className={`timeline-bar ${toneClass[item.tone || 'blue']}`}
                style={{ height: `${Math.max((item.value / max) * 100, item.value > 0 ? 10 : 0)}%` }}
              />
            </div>
            <strong>{formatValue(item.value)}</strong>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
