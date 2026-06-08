type StatusTone = 'success' | 'warning' | 'danger' | 'neutral' | 'info';

export default function StatusBadge({
  label,
  tone = 'neutral',
  dot = false,
}: {
  label: string;
  tone?: StatusTone;
  dot?: boolean;
}) {
  return (
    <span className={`bb-status-badge bb-status-badge-${tone}`}>
      {dot ? <span className="bb-status-badge-dot" aria-hidden="true" /> : null}
      {label}
    </span>
  );
}
