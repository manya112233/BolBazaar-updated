import { useEffect, useMemo, useRef, useState } from 'react';
import {
  createDemoListing,
  fetchInsight,
  fetchListings,
  fetchNotifications,
  fetchOrders,
  fetchSellerDashboard,
  fetchSellerLedger,
  fetchSellers,
  placeOrder,
  recordLedgerPayment,
  reportBuyerDemandSearch,
  resetDemo,
  respondToOrder,
} from './api';
import AuthModal from './components/AuthModal';
import BuyerWorkspace from './components/BuyerWorkspace';
import LandingPage from './components/LandingPage';
import OrderModal from './components/OrderModal';
import SellerWorkspace from './components/SellerWorkspace';
import DashboardLayout, { type DashboardSection } from './components/dashboard/DashboardLayout';
import type { AuthRole, AuthSession, Insight, Listing, Notification, Order, SellerDashboard, SellerLedgerView, SellerProfile } from './types';

const BUYER_SESSION_STORAGE_KEY = 'bolbazaar_buyer_session_id';
const APP_SESSION_STORAGE_KEY = 'bolbazaar_web_session';
const APP_LANGUAGE_STORAGE_KEY = 'bolbazaar_language';

export type AppLanguage = 'en' | 'hi';

function getStoredLanguage(): AppLanguage {
  if (typeof window === 'undefined') {
    return 'en';
  }

  return window.localStorage.getItem(APP_LANGUAGE_STORAGE_KEY) === 'hi' ? 'hi' : 'en';
}

function getOrCreateBuyerSessionId(): string {
  const fallback = `buyer-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  if (typeof window === 'undefined') {
    return fallback;
  }

  try {
    const existing = window.localStorage.getItem(BUYER_SESSION_STORAGE_KEY);
    if (existing && existing.trim()) {
      return existing;
    }

    const nextId = typeof window.crypto?.randomUUID === 'function'
      ? `buyer-${window.crypto.randomUUID()}`
      : fallback;
    window.localStorage.setItem(BUYER_SESSION_STORAGE_KEY, nextId);
    return nextId;
  } catch {
    return fallback;
  }
}

function getStoredSession(): AuthSession | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(APP_SESSION_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as AuthSession;
  } catch {
    return null;
  }
}

function sessionSellerId(session: AuthSession | null): string | null {
  if (!session || session.role !== 'seller') {
    return null;
  }
  return session.seller_id || session.phone_number;
}

export default function App() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [sellers, setSellers] = useState<SellerProfile[]>([]);
  const [dashboard, setDashboard] = useState<SellerDashboard | null>(null);
  const [ledger, setLedger] = useState<SellerLedgerView | null>(null);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [selectedSellerId, setSelectedSellerId] = useState<string | null>(null);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [query, setQuery] = useState('');
  const [sellerSearch, setSellerSearch] = useState('');
  const [maxPrice, setMaxPrice] = useState(100);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<AuthSession | null>(getStoredSession);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authInitialRole, setAuthInitialRole] = useState<AuthRole | null>(null);
  const [language, setLanguage] = useState<AppLanguage>(getStoredLanguage);
  const [buyerSection, setBuyerSection] = useState('marketplace');
  const [sellerSection, setSellerSection] = useState('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const buyerSessionIdRef = useRef<string>(getOrCreateBuyerSessionId());

  const activeSellerId = sessionSellerId(session) || selectedSellerId;

  const loadAll = async (preferredSellerId?: string | null) => {
    setLoading(true);
    setError(null);
    try {
      const [nextListings, nextOrders, nextNotifications, nextSellers] = await Promise.all([
        fetchListings(),
        fetchOrders(),
        fetchNotifications(),
        fetchSellers(),
      ]);

      setListings(nextListings);
      setOrders(nextOrders);
      setNotifications(nextNotifications);
      setSellers(nextSellers);

      const nextSellerId =
        preferredSellerId ||
        sessionSellerId(session) ||
        selectedSellerId ||
        nextSellers[0]?.seller_id ||
        nextListings[0]?.seller_id ||
        nextNotifications[0]?.seller_id ||
        null;

      setSelectedSellerId(nextSellerId);

      if (nextSellerId) {
        const [nextDashboard, nextLedger, nextInsight] = await Promise.all([
          fetchSellerDashboard(nextSellerId),
          fetchSellerLedger(nextSellerId),
          fetchInsight(nextSellerId),
        ]);
        setDashboard(nextDashboard);
        setLedger(nextLedger);
        setInsight(nextInsight);
      } else {
        setDashboard(null);
        setLedger(null);
        setInsight(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadAll();
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      if (session) {
        window.localStorage.setItem(APP_SESSION_STORAGE_KEY, JSON.stringify(session));
      } else {
        window.localStorage.removeItem(APP_SESSION_STORAGE_KEY);
      }
    } catch {
      // Ignore local storage failures and keep the in-memory session.
    }
  }, [session]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    window.localStorage.setItem(APP_LANGUAGE_STORAGE_KEY, language);
  }, [language]);

  useEffect(() => {
    const sellerId = sessionSellerId(session);
    if (sellerId) {
      setSelectedSellerId(sellerId);
      setSellerSection('overview');
      void loadAll(sellerId);
    }
    if (session?.role === 'buyer') {
      setBuyerSection('marketplace');
    }
  }, [session]);

  useEffect(() => {
    const searchQuery = query.trim();
    if (!session || session.role !== 'buyer' || searchQuery.length < 2) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      void reportBuyerDemandSearch({
        buyer_id: buyerSessionIdRef.current,
        search_query: searchQuery,
        max_price_per_kg: maxPrice > 0 ? maxPrice : undefined,
      }).catch((err) => {
        console.warn('Failed to report buyer demand search', err);
      });
    }, 700);

    return () => window.clearTimeout(timeoutId);
  }, [maxPrice, query, session]);

  const filteredListings = useMemo(() => {
    return listings.filter((listing) => {
      const matchesQuery = `${listing.product_name} ${listing.seller_name} ${listing.pickup_location}`
        .toLowerCase()
        .includes(query.toLowerCase());
      const matchesPrice = listing.price_per_kg <= maxPrice;
      return matchesQuery && matchesPrice;
    });
  }, [listings, maxPrice, query]);

  const filteredSellerOrders = useMemo(() => {
    const activeOrders = orders.filter((order) => order.seller_id === activeSellerId);
    const search = sellerSearch.trim().toLowerCase();
    if (!search) return activeOrders;
    return activeOrders.filter((order) =>
      `${order.product_name} ${order.buyer_name} ${order.pickup_time}`.toLowerCase().includes(search),
    );
  }, [activeSellerId, orders, sellerSearch]);

  const filteredSellerNotifications = useMemo(() => {
    const sellerNotes = notifications.filter((note) => note.seller_id === activeSellerId);
    const search = sellerSearch.trim().toLowerCase();
    if (!search) return sellerNotes;
    return sellerNotes.filter((note) => note.text.toLowerCase().includes(search));
  }, [activeSellerId, notifications, sellerSearch]);

  const currentSeller = activeSellerId ? sellers.find((seller) => seller.seller_id === activeSellerId) || null : null;

  const unreadNotifications = useMemo(
    () => notifications.filter((note) => note.delivery_status !== 'failed').length,
    [notifications],
  );

  const buyerSections: DashboardSection[] = [
    { id: 'marketplace', label: 'Marketplace', icon: 'marketplace' },
    { id: 'orders', label: 'Orders', icon: 'orders', badge: orders.filter((order) => order.status === 'pending').length },
    { id: 'sellers', label: 'Trusted Sellers', icon: 'sellers' },
    { id: 'demand', label: 'Demand Signals', icon: 'demand' },
  ];

  const sellerSections: DashboardSection[] = [
    { id: 'overview', label: 'Overview', icon: 'overview' },
    { id: 'listings', label: 'Live Listings', icon: 'listings' },
    { id: 'orders', label: 'Orders', icon: 'orders', badge: filteredSellerOrders.filter((order) => order.status === 'pending').length },
    { id: 'ledger', label: 'Khata Ledger', icon: 'ledger' },
    { id: 'insights', label: 'AI Insights', icon: 'insights' },
    { id: 'profile', label: 'Verification/Profile', icon: 'profile' },
  ];

  const currentSections = session?.role === 'seller' ? sellerSections : buyerSections;
  const currentSectionId = session?.role === 'seller' ? sellerSection : buyerSection;

  const sectionScopedBuyerListings = useMemo(() => {
    if (buyerSection === 'sellers' && selectedSellerId) {
      return filteredListings.filter((listing) => listing.seller_id === selectedSellerId);
    }
    return filteredListings;
  }, [buyerSection, filteredListings, selectedSellerId]);

  const sectionScopedBuyerOrders = useMemo(() => {
    if (buyerSection === 'orders') return orders;
    return orders;
  }, [buyerSection, orders]);

  const sectionScopedBuyerSellers = useMemo(() => {
    if (buyerSection === 'sellers' && selectedSellerId) {
      return sellers.filter((seller) => seller.seller_id === selectedSellerId);
    }
    return sellers;
  }, [buyerSection, selectedSellerId, sellers]);

  const sectionScopedSellerOrders = useMemo(() => {
    if (sellerSection === 'orders') return filteredSellerOrders;
    return filteredSellerOrders;
  }, [filteredSellerOrders, sellerSection]);

  const sectionScopedSellerNotifications = useMemo(() => {
    if (sellerSection === 'insights') return filteredSellerNotifications;
    return filteredSellerNotifications;
  }, [filteredSellerNotifications, sellerSection]);

  return (
    <div className="app-shell">
      {error && (
        <div className="page-shell">
          <div className="error-banner">{error}</div>
        </div>
      )}

      {!session && (
        <LandingPage
          language={language}
          onLanguageChange={setLanguage}
          stats={{
            liveListings: listings.length,
            activeSellers: sellers.length,
            acceptedOrders: orders.filter((order) => order.status === 'accepted' || order.status === 'completed').length,
            alertsSent: notifications.length,
          }}
          onOpenLogin={(role) => {
            setAuthInitialRole(role);
            setAuthModalOpen(true);
          }}
        />
      )}

      {session && (
        <DashboardLayout
          brand="BolBazaar"
          role={session.role}
          sectionId={currentSectionId}
          sections={currentSections}
          onNavigate={(nextSection) => {
            if (session.role === 'seller') {
              setSellerSection(nextSection);
            } else {
              setBuyerSection(nextSection);
            }
            setMobileSidebarOpen(false);
          }}
          isSidebarCollapsed={sidebarCollapsed}
          onToggleSidebar={() => setSidebarCollapsed((value) => !value)}
          mobileSidebarOpen={mobileSidebarOpen}
          onToggleMobileSidebar={() => setMobileSidebarOpen((value) => !value)}
          searchValue={session.role === 'buyer' ? query : sellerSearch}
          onSearchChange={session.role === 'buyer' ? setQuery : setSellerSearch}
          searchPlaceholder={
            session.role === 'buyer'
              ? 'Search produce, sellers, pickup area...'
              : 'Search orders, buyers, ledger context...'
          }
          language={language}
          onLanguageChange={setLanguage}
          unreadNotifications={unreadNotifications}
          sessionLabel={session.role === 'seller' ? 'Seller session' : 'Buyer session'}
          onLogout={() => setSession(null)}
        >
          {session.role === 'buyer' ? (
            <BuyerWorkspace
              sectionId={buyerSection}
              language={language}
              session={session}
              listings={sectionScopedBuyerListings}
              sellers={sectionScopedBuyerSellers}
              orders={sectionScopedBuyerOrders}
              notifications={notifications}
              dashboard={dashboard}
              insight={insight}
              selectedSellerId={activeSellerId}
              query={query}
              maxPrice={maxPrice}
              loading={loading}
              onSelectSeller={(sellerId) => {
                setSelectedSellerId(sellerId);
                setBuyerSection('sellers');
                void loadAll(sellerId);
              }}
              onQueryChange={setQuery}
              onMaxPriceChange={setMaxPrice}
              onOrder={setSelectedListing}
            />
          ) : (
            <SellerWorkspace
              sectionId={sellerSection}
              language={language}
              session={session}
              seller={currentSeller}
              dashboard={dashboard}
              ledger={ledger}
              orders={sectionScopedSellerOrders}
              notifications={sectionScopedSellerNotifications}
              insight={insight}
              loading={loading}
              onRespondOrder={async (orderId, decision) => {
                await respondToOrder(orderId, decision);
                await loadAll(activeSellerId);
              }}
              onRecordLedgerPayment={async (payload) => {
                if (!activeSellerId) {
                  throw new Error('Seller session not available');
                }
                await recordLedgerPayment({ seller_id: activeSellerId, ...payload });
                await loadAll(activeSellerId);
              }}
            />
          )}
        </DashboardLayout>
      )}

      {selectedListing && session?.role === 'buyer' && (
        <OrderModal
          listing={selectedListing}
          defaultBuyerName={`Buyer ${session.phone_number.slice(-4)}`}
          defaultBuyerPhone={session.phone_number}
          onClose={() => setSelectedListing(null)}
          onSubmit={async (payload) => {
            await placeOrder({ listing_id: selectedListing.id, ...payload });
            setSelectedListing(null);
            await loadAll(activeSellerId);
          }}
        />
      )}

      <AuthModal
        language={language}
        onLanguageChange={setLanguage}
        isOpen={authModalOpen}
        initialRole={authInitialRole}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={(nextSession) => {
          setSession(nextSession);
          setAuthModalOpen(false);
        }}
      />

      {session?.role === 'buyer' && (
        <button
          type="button"
          className="floating-demo-button"
          onClick={() => {
            void (async () => {
              await resetDemo();
              await createDemoListing();
              await loadAll(activeSellerId);
            })();
          }}
        >
          Reset demo
        </button>
      )}
    </div>
  );
}
