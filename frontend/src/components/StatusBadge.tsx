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
    <span className={`status-badge status-badge-${tone}`}>
      {dot && <span className="status-badge-dot" aria-hidden="true" />}
      {label}
    </span>
  );
}
