import './DashboardLayout.css';
import type { ReactNode } from 'react';
import NotificationCenter from '../NotificationCenter';
import { t, type Language } from '../../i18n';
import type { Notification } from '../../types';

type DashboardIcon =
  | 'marketplace'
  | 'orders'
  | 'sellers'
  | 'demand'
  | 'overview'
  | 'listings'
  | 'ledger'
  | 'insights'
  | 'profile';

export type DashboardSection = {
  id: string;
  label: string;
  icon: DashboardIcon;
  badge?: number;
};

function titleFor(role: 'buyer' | 'seller' | 'ops', sectionId: string) {
  if (role === 'seller') {
    return (
      {
        overview: 'Overview',
        listings: 'Listings',
        orders: 'Orders',
        ledger: 'Khata Ledger',
        insights: 'AI Insights',
        profile: 'Verification',
      }[sectionId] || 'Seller Dashboard'
    );
  }

  if (role === 'ops') {
    return (
      {
        quality: 'Ops Verification',
        deliveries: 'Managed Delivery',
        metrics: 'Smart Supply Chain',
      }[sectionId] || 'Ops Dashboard'
    );
  }

  return (
    {
      marketplace: 'Marketplace',
      orders: 'Orders',
      sellers: 'Sellers',
      demand: 'Demand Signals',
    }[sectionId] || 'Buyer Dashboard'
  );
}

function Icon({
  name,
}: {
  name: DashboardIcon | 'menu' | 'close' | 'search' | 'bell' | 'collapse';
}) {
  const props = {
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  };

  switch (name) {
    case 'menu':
      return <svg {...props}><path d="M4 7h16M4 12h16M4 17h16" /></svg>;
    case 'close':
      return <svg {...props}><path d="m6 6 12 12M18 6 6 18" /></svg>;
    case 'search':
      return <svg {...props}><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4 4" /></svg>;
    case 'bell':
      return <svg {...props}><path d="M15 17H5.5a1 1 0 0 1-.82-1.57A6.9 6.9 0 0 0 6 11.5V10a6 6 0 1 1 12 0v1.5a6.9 6.9 0 0 0 1.32 3.93A1 1 0 0 1 18.5 17H15" /><path d="M9.5 20a2.5 2.5 0 0 0 5 0" /></svg>;
    case 'collapse':
      return <svg {...props}><path d="M15 6 9 12l6 6" /></svg>;
    case 'marketplace':
      return <svg {...props}><path d="M4 9h16" /><path d="M6 9V7a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2" /><path d="M5 9h14l-1 9a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2Z" /></svg>;
    case 'orders':
      return <svg {...props}><path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01" /></svg>;
    case 'sellers':
      return <svg {...props}><circle cx="9" cy="8" r="3.5" /><path d="M3.5 20a5.5 5.5 0 0 1 11 0" /><path d="M17 11a3 3 0 1 0 0-6" /><path d="M20.5 20a4.5 4.5 0 0 0-3.5-4.38" /></svg>;
    case 'demand':
      return <svg {...props}><path d="M4 18a8 8 0 1 1 16 0" /><path d="M8 18a4 4 0 1 1 8 0" /><path d="M12 18h.01" /></svg>;
    case 'overview':
      return <svg {...props}><path d="M4 13h7V4H4Z" /><path d="M13 20h7v-9h-7Z" /><path d="M13 10h7V4h-7Z" /><path d="M4 20h7v-5H4Z" /></svg>;
    case 'listings':
      return <svg {...props}><path d="M6 4h12v16H6z" /><path d="M9 8h6M9 12h6M9 16h4" /></svg>;
    case 'ledger':
      return <svg {...props}><path d="M6 4h12a1 1 0 0 1 1 1v15l-3-2-4 2-4-2-3 2V5a1 1 0 0 1 1-1Z" /><path d="M9 9h6M9 13h4" /></svg>;
    case 'insights':
      return <svg {...props}><path d="M12 3v6" /><path d="M8 11h8" /><path d="M9 21h6" /><path d="M7 17a5 5 0 1 1 10 0c0 1.36-.55 2.6-1.45 3.5h-7.1A4.97 4.97 0 0 1 7 17Z" /></svg>;
    case 'profile':
      return <svg {...props}><circle cx="12" cy="8" r="4" /><path d="M5 20a7 7 0 0 1 14 0" /><path d="m17.5 6.5 1 1 2-2" /></svg>;
  }
}

export default function DashboardLayout({
  brand,
  role,
  sectionId,
  sections,
  onNavigate,
  isSidebarCollapsed,
  onToggleSidebar,
  mobileSidebarOpen,
  onToggleMobileSidebar,
  searchValue,
  onSearchChange,
  searchPlaceholder,
  language,
  onLanguageChange,
  unreadNotifications,
  notifications,
  notificationOpen,
  onToggleNotifications,
  onMarkNotificationRead,
  onMarkAllNotificationsRead,
  sessionLabel,
  onLogout,
  children,
}: {
  brand: string;
  role: 'buyer' | 'seller' | 'ops';
  sectionId: string;
  sections: DashboardSection[];
  onNavigate: (id: string) => void;
  isSidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  mobileSidebarOpen: boolean;
  onToggleMobileSidebar: () => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder: string;
  language: Language;
  onLanguageChange: (language: Language) => void;
  unreadNotifications: number;
  notifications: Notification[];
  notificationOpen: boolean;
  onToggleNotifications: () => void;
  onMarkNotificationRead: (notificationId: string) => Promise<void>;
  onMarkAllNotificationsRead: () => Promise<void>;
  sessionLabel: string;
  onLogout: () => void;
  children: ReactNode;
}) {
  const pageTitle = titleFor(role, sectionId);
  const mobileRoleLabel = role === 'seller'
    ? t(language, 'dashboard.sellerDashboard')
    : role === 'ops'
      ? t(language, 'dashboard.opsDashboard')
      : t(language, 'dashboard.buyerDashboard');
  const networkLabel = role === 'seller'
    ? t(language, 'dashboard.sellerNetwork')
    : role === 'ops'
      ? t(language, 'dashboard.opsNetwork')
      : t(language, 'dashboard.buyerNetwork');

  return (
    <div className="bb-shell">
      <aside className={`bb-sidebar ${isSidebarCollapsed ? 'is-collapsed' : ''}`}>
        <div className="bb-sidebar-brand">
          <button type="button" className="bb-sidebar-brand-button" onClick={onToggleSidebar} aria-label={t(language, 'dashboard.toggleSidebar')}>
            <span className="bb-sidebar-brand-mark">BB</span>
            <span className="bb-sidebar-brand-copy">
              <strong>{brand}</strong>
              <small>{role === 'seller' ? t(language, 'dashboard.sellerOs') : role === 'ops' ? t(language, 'dashboard.opsOs') : t(language, 'dashboard.buyerOs')}</small>
            </span>
            <span className={`bb-sidebar-collapse ${isSidebarCollapsed ? 'is-collapsed' : ''}`}><Icon name="collapse" /></span>
          </button>
        </div>

        <nav className="bb-sidebar-nav" aria-label={`${role} navigation`}>
          {sections.map((section) => (
            <button
              key={section.id}
              type="button"
              className={`bb-sidebar-link ${section.id === sectionId ? 'is-active' : ''}`}
              onClick={() => onNavigate(section.id)}
              title={section.label}
            >
              <span className="bb-sidebar-link-icon"><Icon name={section.icon} /></span>
              <span className="bb-sidebar-link-copy">
                <span>{section.label}</span>
                {section.badge ? <small>{section.badge}</small> : null}
              </span>
            </button>
          ))}
        </nav>

        <div className="bb-sidebar-footer">
          <div className="bb-sidebar-note">
            <span className="bb-sidebar-note-label">{t(language, 'dashboard.whatsAppFirst')}</span>
            <strong>{t(language, 'dashboard.liveOps')}</strong>
            <p>{t(language, 'dashboard.whatsAppBody')}</p>
          </div>
        </div>
      </aside>

      <div className={`bb-mobile-overlay ${mobileSidebarOpen ? 'is-open' : ''}`} onClick={onToggleMobileSidebar} />
      <aside className={`bb-mobile-sidebar ${mobileSidebarOpen ? 'is-open' : ''}`}>
        <div className="bb-mobile-head">
          <div>
            <strong>{brand}</strong>
            <small>{mobileRoleLabel}</small>
          </div>
          <button type="button" className="bb-icon-button" onClick={onToggleMobileSidebar} aria-label={t(language, 'dashboard.closeNavigation')}>
            <Icon name="close" />
          </button>
        </div>
        <nav className="bb-sidebar-nav">
          {sections.map((section) => (
            <button
              key={section.id}
              type="button"
              className={`bb-sidebar-link ${section.id === sectionId ? 'is-active' : ''}`}
              onClick={() => {
                onNavigate(section.id);
                onToggleMobileSidebar();
              }}
            >
              <span className="bb-sidebar-link-icon"><Icon name={section.icon} /></span>
              <span className="bb-sidebar-link-copy">
                <span>{section.label}</span>
                {section.badge ? <small>{section.badge}</small> : null}
              </span>
            </button>
          ))}
        </nav>
      </aside>

      <div className="bb-main">
        <header className="bb-topbar">
          <div className="bb-topbar-leading">
            <button type="button" className="bb-icon-button bb-mobile-only" onClick={onToggleMobileSidebar} aria-label={t(language, 'dashboard.openNavigation')}>
              <Icon name="menu" />
            </button>
            <div className="bb-page-title">
              <span>{networkLabel}</span>
              <strong>{pageTitle}</strong>
            </div>
          </div>

          <div className="bb-topbar-actions">
            <label className="bb-search">
              <span className="bb-search-icon"><Icon name="search" /></span>
              <input
                value={searchValue}
                onChange={(event) => onSearchChange(event.target.value)}
                placeholder={searchPlaceholder}
                aria-label={t(language, 'dashboard.searchWorkspace')}
              />
            </label>

            <div className="language-switcher" aria-label={t(language, 'dashboard.languageSwitcher')}>
              <button type="button" className={language === 'en' ? 'language-switch-active' : ''} onClick={() => onLanguageChange('en')}>EN</button>
              <button type="button" className={language === 'hi' ? 'language-switch-active' : ''} onClick={() => onLanguageChange('hi')}>HI</button>
            </div>

            <button type="button" className="bb-icon-button" aria-label={t(language, 'common.notifications')} onClick={onToggleNotifications}>
              <Icon name="bell" />
              {unreadNotifications > 0 ? <span className="bb-notification-count">{Math.min(unreadNotifications, 9)}</span> : null}
            </button>

            <span className="bb-session-chip">{sessionLabel}</span>
            <button type="button" className="ghost-button small" onClick={onLogout}>{t(language, 'common.logout')}</button>
          </div>
        </header>

        <NotificationCenter
          open={notificationOpen}
          language={language}
          notifications={notifications}
          onClose={onToggleNotifications}
          onMarkRead={onMarkNotificationRead}
          onMarkAllRead={onMarkAllNotificationsRead}
        />

        <main className="bb-content">{children}</main>
      </div>
    </div>
  );
}
