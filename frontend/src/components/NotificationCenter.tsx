import type { Notification } from '../types';
import type { Language } from '../i18n';
import { t } from '../i18n';

function formatTime(value: string): string {
  try {
    return new Date(value).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
  } catch {
    return value;
  }
}

export default function NotificationCenter({
  open,
  language,
  notifications,
  onClose,
  onMarkRead,
  onMarkAllRead,
}: {
  open: boolean;
  language: Language;
  notifications: Notification[];
  onClose: () => void;
  onMarkRead: (notificationId: string) => Promise<void>;
  onMarkAllRead: () => Promise<void>;
}) {
  if (!open) return null;

  return (
    <div className="bb-notification-drawer">
      <div className="bb-notification-head">
        <div>
          <strong>{t(language, 'notifications.title')}</strong>
          <p>{notifications.length} {t(language, 'common.items')}</p>
        </div>
        <div className="action-row">
          <button type="button" className="ghost-button small" onClick={() => void onMarkAllRead()}>
            {t(language, 'common.markAllRead')}
          </button>
          <button type="button" className="ghost-button small" onClick={onClose}>
            {t(language, 'common.close')}
          </button>
        </div>
      </div>

      {notifications.length === 0 ? (
        <div className="bb-empty-state">
          <strong>{t(language, 'common.noNotifications')}</strong>
        </div>
      ) : (
        <div className="bb-notification-list">
          {notifications.map((item) => (
            <article key={item.id} className={`bb-notification-item ${item.read_at ? 'is-read' : 'is-unread'}`}>
              <div className="bb-notification-meta">
                <strong>{item.title}</strong>
                <span>{formatTime(item.created_at)}</span>
              </div>
              <p>{item.body || item.text}</p>
              <div className="bb-notification-actions">
                <span className="bb-session-chip">{item.category}</span>
                {!item.read_at ? (
                  <button type="button" className="ghost-button small" onClick={() => void onMarkRead(item.id)}>
                    {t(language, 'common.markRead')}
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
