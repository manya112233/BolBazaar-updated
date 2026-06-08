import StatusBadge from './StatusBadge';

export type TimelineItem = {
  title: string;
  body: string;
  meta?: string;
  tone?: 'success' | 'warning' | 'danger' | 'neutral' | 'info';
  badge?: string;
};

export default function ActivityTimeline({
  items,
  emptyTitle,
  emptyBody,
}: {
  items: TimelineItem[];
  emptyTitle: string;
  emptyBody: string;
}) {
  if (items.length === 0) {
    return (
      <div className="bb-empty-state">
        <strong>{emptyTitle}</strong>
        <p>{emptyBody}</p>
      </div>
    );
  }

  return (
    <div className="bb-timeline">
      {items.map((item) => (
        <article key={`${item.title}-${item.body}-${item.meta || ''}`} className="bb-timeline-item">
          <div className={`bb-timeline-dot bb-timeline-dot-${item.tone || 'neutral'}`} aria-hidden="true" />
          <div className="bb-timeline-copy">
            <div className="bb-timeline-head">
              <strong>{item.title}</strong>
              {item.badge ? <StatusBadge label={item.badge} tone={item.tone || 'neutral'} /> : null}
            </div>
            <p>{item.body}</p>
            {item.meta ? <span className="bb-timeline-meta">{item.meta}</span> : null}
          </div>
        </article>
      ))}
    </div>
  );
}
