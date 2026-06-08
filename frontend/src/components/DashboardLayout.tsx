import './DashboardLayout.css';
import type { ReactNode } from 'react';

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

function dashboardTitle(sectionId: string, role: 'buyer' | 'seller') {
  if (role === 'seller') {
    const titles: Record<string, string> = {
      overview: 'Seller Overview',
      listings: 'Live Listings',
      orders: 'Orders Queue',
      ledger: 'Khata Ledger',
      insights: 'AI Insights',
      profile: 'Verification & Profile',
    };
    return titles[sectionId] || 'Seller Workspace';
  }

  const titles: Record<string, string> = {
    marketplace: 'Marketplace',
    orders: 'Buyer Orders',
    sellers: 'Trusted Sellers',
    demand: 'Demand Signals',
  };
  return titles[sectionId] || 'Buyer Workspace';
}

function Icon({
  name,
  className = '',
}: {
  name: DashboardIcon | 'menu' | 'search' | 'bell' | 'collapse' | 'close';
  className?: string;
}) {
  const commonProps = {
    className,
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
      return (
        <svg {...commonProps}>
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      );
    case 'search':
      return (
        <svg {...commonProps}>
          <circle cx="11" cy="11" r="6.5" />
          <path d="m16 16 4 4" />
        </svg>
      );
    case 'bell':
      return (
        <svg {...commonProps}>
          <path d="M15 17H5.5a1 1 0 0 1-.82-1.57A6.9 6.9 0 0 0 6 11.5V10a6 6 0 1 1 12 0v1.5a6.9 6.9 0 0 0 1.32 3.93A1 1 0 0 1 18.5 17H15" />
          <path d="M9.5 20a2.5 2.5 0 0 0 5 0" />
        </svg>
      );
    case 'collapse':
      return (
        <svg {...commonProps}>
          <path d="M15 6 9 12l6 6" />
        </svg>
      );
    case 'close':
      return (
        <svg {...commonProps}>
          <path d="m6 6 12 12M18 6 6 18" />
        </svg>
      );
    case 'marketplace':
      return (
        <svg {...commonProps}>
          <path d="M4 10h16" />
          <path d="M6 10V7.5a1.5 1.5 0 0 1 1.5-1.5h9A1.5 1.5 0 0 1 18 7.5V10" />
          <path d="M5 10h14l-1 8a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2Z" />
        </svg>
      );
    case 'orders':
      return (
        <svg {...commonProps}>
          <path d="M8 6h12" />
          <path d="M8 12h12" />
          <path d="M8 18h12" />
          <path d="M4 6h.01M4 12h.01M4 18h.01" />
        </svg>
      );
    case 'sellers':
      return (
        <svg {...commonProps}>
          <path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2" />
          <circle cx="9.5" cy="7" r="3.5" />
          <path d="M17 11a3 3 0 1 0 0-6" />
          <path d="M21 21v-2a4 4 0 0 0-3-3.87" />
        </svg>
      );
    case 'demand':
      return (
        <svg {...commonProps}>
          <path d="M4 18a8 8 0 1 1 16 0" />
          <path d="M8 18a4 4 0 1 1 8 0" />
          <path d="M12 18h.01" />
        </svg>
      );
    case 'overview':
      return (
        <svg {...commonProps}>
          <path d="M4 13h7V4H4Z" />
          <path d="M13 20h7v-9h-7Z" />
          <path d="M13 10h7V4h-7Z" />
          <path d="M4 20h7v-5H4Z" />
        </svg>
      );
    case 'listings':
      return (
        <svg {...commonProps}>
          <path d="M6 4h12v16H6z" />
          <path d="M9 8h6M9 12h6M9 16h4" />
        </svg>
      );
    case 'ledger':
      return (
        <svg {...commonProps}>
          <path d="M5 4h12a2 2 0 0 1 2 2v14l-3-2-3 2-3-2-3 2V6a2 2 0 0 1 2-2Z" />
          <path d="M9 9h6M9 13h4" />
        </svg>
      );
    case 'insights':
      return (
        <svg {...commonProps}>
          <path d="M12 3v6" />
          <path d="M8 11h8" />
          <path d="M8.5 21h7" />
          <path d="M7 17a5 5 0 1 1 10 0c0 1.27-.46 2.43-1.22 3.33H8.22A4.96 4.96 0 0 1 7 17Z" />
        </svg>
      );
    case 'profile':
      return (
        <svg {...commonProps}>
          <circle cx="12" cy="8" r="4" />
          <path d="M5 20a7 7 0 0 1 14 0" />
          <path d="m18.5 6.5 1 1 2-2" />
        </svg>
      );
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
  sessionLabel,
  onLogout,
  children,
}: {
  brand: string;
  role: 'buyer' | 'seller';
  sectionId: string;
  sections: DashboardSection[];
  onNavigate: (sectionId: string) => void;
  isSidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  mobileSidebarOpen: boolean;
  onToggleMobileSidebar: () => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder: string;
  language: 'en' | 'hi';
  onLanguageChange: (language: 'en' | 'hi') => void;
  unreadNotifications: number;
  sessionLabel: string;
  onLogout: () => void;
  children: ReactNode;
}) {
  return (
    <div className="dashboard-shell">
      <aside className={`dashboard-sidebar ${isSidebarCollapsed ? 'is-collapsed' : ''}`}>
        <div className="dashboard-sidebar-brand">
          <button className="dashboard-brand-button" type="button" onClick={onToggleSidebar} aria-label="Toggle sidebar">
            <span className="dashboard-brand-mark">BB</span>
            <span className="dashboard-brand-copy">
              <strong>{brand}</strong>
              <small>{role === 'seller' ? 'Seller operating system' : 'Buyer operating system'}</small>
            </span>
            <Icon name="collapse" className={`dashboard-collapse-icon ${isSidebarCollapsed ? 'is-collapsed' : ''}`} />
          </button>
        </div>

        <nav className="dashboard-sidebar-nav" aria-label={`${role} navigation`}>
          {sections.map((section) => {
            const active = section.id === sectionId;
            return (
              <button
                key={section.id}
                type="button"
                className={`dashboard-nav-item ${active ? 'is-active' : ''}`}
                onClick={() => onNavigate(section.id)}
                title={section.label}
              >
                <span className="dashboard-nav-icon" aria-hidden="true">
                  <Icon name={section.icon} />
                </span>
                <span className="dashboard-nav-copy">
                  <span>{section.label}</span>
                  {typeof section.badge === 'number' && section.badge > 0 ? <small>{section.badge}</small> : null}
                </span>
              </button>
            );
          })}
        </nav>

        <div className="dashboard-sidebar-footer">
          <div className="dashboard-market-signal">
            <span className="sidebar-panel-label">Operations</span>
            <strong>WhatsApp-first trade sync</strong>
            <p>Listings, khata, verification, and order prompts remain tied to the seller phone workflow.</p>
          </div>
        </div>
      </aside>

      <div className={`dashboard-mobile-overlay ${mobileSidebarOpen ? 'is-open' : ''}`} onClick={onToggleMobileSidebar} />

      <aside className={`dashboard-mobile-sidebar ${mobileSidebarOpen ? 'is-open' : ''}`}>
        <div className="dashboard-mobile-head">
          <div>
            <strong>{brand}</strong>
            <small>{role === 'seller' ? 'Seller workspace' : 'Buyer workspace'}</small>
          </div>
          <button type="button" className="topbar-icon-button" onClick={onToggleMobileSidebar} aria-label="Close navigation">
            <Icon name="close" />
          </button>
        </div>
        <nav className="dashboard-mobile-nav" aria-label={`${role} mobile navigation`}>
          {sections.map((section) => (
            <button
              key={section.id}
              type="button"
              className={`dashboard-nav-item ${section.id === sectionId ? 'is-active' : ''}`}
              onClick={() => {
                onNavigate(section.id);
                onToggleMobileSidebar();
              }}
            >
              <span className="dashboard-nav-icon" aria-hidden="true">
                <Icon name={section.icon} />
              </span>
              <span className="dashboard-nav-copy">
                <span>{section.label}</span>
                {typeof section.badge === 'number' && section.badge > 0 ? <small>{section.badge}</small> : null}
              </span>
            </button>
          ))}
        </nav>
      </aside>

      <div className="dashboard-main">
        <header className="dashboard-topbar">
          <div className="dashboard-topbar-leading">
            <button type="button" className="topbar-icon-button mobile-only" onClick={onToggleMobileSidebar} aria-label="Open navigation">
              <Icon name="menu" />
            </button>
            <div className="dashboard-topbar-title">
              <span className="dashboard-topbar-kicker">{role === 'seller' ? 'Seller network' : 'Buyer network'}</span>
              <strong>{dashboardTitle(sectionId, role)}</strong>
            </div>
          </div>

          <div className="dashboard-topbar-actions">
            <label className="dashboard-search">
              <Icon name="search" className="dashboard-inline-icon" />
              <input
                value={searchValue}
                onChange={(event) => onSearchChange(event.target.value)}
                placeholder={searchPlaceholder}
                aria-label="Workspace search"
              />
            </label>

            <div className="language-switcher" aria-label="Language switcher">
              <button type="button" className={language === 'en' ? 'language-switch-active' : ''} onClick={() => onLanguageChange('en')}>
                EN
              </button>
              <button type="button" className={language === 'hi' ? 'language-switch-active' : ''} onClick={() => onLanguageChange('hi')}>
                HI
              </button>
            </div>

            <button type="button" className="topbar-icon-button" aria-label="Notifications">
              <Icon name="bell" />
              {unreadNotifications > 0 ? <span className="topbar-notification-dot">{Math.min(unreadNotifications, 9)}</span> : null}
            </button>

            <span className="dashboard-session-chip">{sessionLabel}</span>
            <button type="button" className="ghost-button small" onClick={onLogout}>
              Logout
            </button>
          </div>
        </header>

        <main className="dashboard-content">{children}</main>
      </div>
    </div>
  );
}
