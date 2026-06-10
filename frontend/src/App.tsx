import { useEffect, useMemo, useRef, useState } from 'react';
import {
  createDemoListing,
  fetchDemandPools,
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
  createDemandRequest,
  fetchBuyerDemandRequests,
  fetchCommitPools,
  commitToPool,
  fetchDeliveries,
  advanceDelivery,
  advanceDeliveryForActor,
  confirmBuyerDelivery,
  fetchOpsDashboard,
  markAllNotificationsRead,
  markNotificationRead,
  updateListingQuality,
} from './api';
import AuthModal from './components/AuthModal';
import BuyerWorkspace from './components/BuyerWorkspace';
import LandingPage from './components/LandingPage';
import OrderModal from './components/OrderModal';
import OpsWorkspace from './components/OpsWorkspace';
import SellerWorkspace from './components/SellerWorkspace';
import DashboardLayout, { type DashboardSection } from './components/dashboard/DashboardLayout';
import { t } from './i18n';
import type { AuthRole, AuthSession, CommitDemandPool, Delivery, DemandPoolOpportunity, DemandRequest, Insight, Listing, Notification, OpsDashboardResponse, Order, SellerDashboard, SellerLedgerView, SellerProfile } from './types';

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

function sessionNotificationFilters(session: AuthSession | null): {
  role?: 'buyer' | 'seller' | 'ops';
  recipient_id?: string;
} {
  if (!session) {
    return {};
  }
  if (session.role === 'seller') {
    return { role: 'seller', recipient_id: session.seller_id || session.phone_number };
  }
  if (session.role === 'buyer') {
    return { role: 'buyer', recipient_id: session.phone_number };
  }
  return { role: 'ops', recipient_id: 'ops-team' };
}

export default function App() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [sellers, setSellers] = useState<SellerProfile[]>([]);
  const [demandPools, setDemandPools] = useState<DemandPoolOpportunity[]>([]);
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
  const [notificationOpen, setNotificationOpen] = useState(false);
  const buyerSessionIdRef = useRef<string>(getOrCreateBuyerSessionId());
  const [buyerDemands, setBuyerDemands] = useState<DemandRequest[]>([]);
  const [buyerDeliveries, setBuyerDeliveries] = useState<Delivery[]>([]);
  const [commitPools, setCommitPools] = useState<CommitDemandPool[]>([]);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [opsDashboard, setOpsDashboard] = useState<OpsDashboardResponse | null>(null);
  const [opsSection, setOpsSection] = useState('quality');

  const activeSellerId = sessionSellerId(session) || selectedSellerId;
  const notificationFilters = sessionNotificationFilters(session);

  const loadAll = async (preferredSellerId?: string | null) => {
    setLoading(true);
    setError(null);
    try {
      const currentSession = session;
      const currentRole = currentSession?.role;
      const buyerId = currentSession?.role === 'buyer' ? currentSession.phone_number : null;
      const nextNotificationFilters = sessionNotificationFilters(currentSession);

      const [nextListings, nextOrders, nextNotifications, nextSellers, nextDemandPools] = await Promise.all([
        fetchListings(),
        fetchOrders(),
        fetchNotifications(nextNotificationFilters),
        fetchSellers(),
        fetchDemandPools(),
      ]);

      setListings(nextListings);
      setOrders(nextOrders);
      setNotifications(nextNotifications);
      setSellers(nextSellers);
      setDemandPools(nextDemandPools);

      if (currentRole === 'ops') {
        const nextOpsDashboard = await fetchOpsDashboard();
        setOpsDashboard(nextOpsDashboard);
        setBuyerDemands([]);
        setBuyerDeliveries([]);
        setDashboard(null);
        setLedger(null);
        setInsight(null);
        setCommitPools([]);
        setDeliveries(nextOpsDashboard.active_deliveries);
        return;
      }

      const nextSellerId =
        preferredSellerId ||
        sessionSellerId(currentSession) ||
        selectedSellerId ||
        nextSellers[0]?.seller_id ||
        nextListings[0]?.seller_id ||
        nextNotifications[0]?.seller_id ||
        null;
      setSelectedSellerId(nextSellerId);

      if (currentRole === 'buyer' && buyerId) {
        const [demands, bDeliveries] = await Promise.all([
          fetchBuyerDemandRequests(buyerId),
          fetchDeliveries({ buyer_id: buyerId })
        ]);
        setBuyerDemands(demands);
        setBuyerDeliveries(bDeliveries);
      } else {
        setBuyerDemands([]);
        setBuyerDeliveries([]);
      }

      if (nextSellerId) {
        const [nextDashboard, nextLedger, nextInsight, pools, sDeliveries] = await Promise.all([
          fetchSellerDashboard(nextSellerId),
          fetchSellerLedger(nextSellerId),
          fetchInsight(nextSellerId),
          fetchCommitPools(nextSellerId),
          fetchDeliveries({ seller_id: nextSellerId }),
        ]);
        setDashboard(nextDashboard);
        setLedger(nextLedger);
        setInsight(nextInsight);
        setCommitPools(pools);
        setDeliveries(sDeliveries);
        setOpsDashboard(null);
      } else {
        setDashboard(null);
        setLedger(null);
        setInsight(null);
        setCommitPools([]);
        setDeliveries([]);
        setOpsDashboard(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load the BolBazaar demo workspace.');
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
    if (session?.role === 'ops') {
      setOpsSection('quality');
      void loadAll(null);
    }
    if (session?.role === 'buyer') {
      setBuyerSection('marketplace');
      void loadAll(null);
    }
  }, [session]);

  useEffect(() => {
    const searchQuery = query.trim();
    if (!session || session.role !== 'buyer' || searchQuery.length < 2) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      const buyerId = session.phone_number || buyerSessionIdRef.current;
      void reportBuyerDemandSearch({
        buyer_id: buyerId,
        search_query: searchQuery,
        max_price_per_kg: maxPrice > 0 ? maxPrice : undefined,
      })
        .then(() => fetchDemandPools())
        .then((items) => setDemandPools(items))
        .catch((err) => {
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
    () => notifications.filter((note) => !note.read_at).length,
    [notifications],
  );

  const buyerSections: DashboardSection[] = [
    { id: 'marketplace', label: t(language, 'dashboard.marketplace'), icon: 'marketplace' },
    { id: 'orders', label: t(language, 'dashboard.orders'), icon: 'orders', badge: orders.filter((order) => order.status === 'pending').length },
    { id: 'sellers', label: t(language, 'dashboard.sellers'), icon: 'sellers' },
    { id: 'demand', label: t(language, 'dashboard.demand'), icon: 'demand' },
  ];

  const sellerSections: DashboardSection[] = [
    { id: 'overview', label: t(language, 'dashboard.overview'), icon: 'overview' },
    { id: 'listings', label: t(language, 'dashboard.listings'), icon: 'listings' },
    { id: 'orders', label: t(language, 'dashboard.orders'), icon: 'orders', badge: filteredSellerOrders.filter((order) => order.status === 'pending').length },
    { id: 'ledger', label: t(language, 'dashboard.ledger'), icon: 'ledger' },
    { id: 'insights', label: t(language, 'dashboard.insights'), icon: 'insights' },
    { id: 'profile', label: t(language, 'dashboard.profile'), icon: 'profile' },
  ];

  const opsSections: DashboardSection[] = [
    { id: 'quality', label: t(language, 'dashboard.opsVerification'), icon: 'listings', badge: opsDashboard?.pending_quality_checks.length },
    { id: 'deliveries', label: t(language, 'dashboard.managedDelivery'), icon: 'orders', badge: opsDashboard?.active_deliveries.length },
    { id: 'metrics', label: t(language, 'dashboard.smartSupplyChain'), icon: 'insights' },
  ];

  const currentSections = session?.role === 'seller' ? sellerSections : session?.role === 'ops' ? opsSections : buyerSections;
  const currentSectionId = session?.role === 'seller' ? sellerSection : session?.role === 'ops' ? opsSection : buyerSection;

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
            } else if (session.role === 'ops') {
              setOpsSection(nextSection);
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
              : session.role === 'ops'
                ? 'Search quality queue, delivery route, seller...'
              : 'Search orders, buyers, ledger context...'
          }
          language={language}
          onLanguageChange={setLanguage}
          unreadNotifications={unreadNotifications}
          notifications={notifications}
          notificationOpen={notificationOpen}
          onToggleNotifications={() => setNotificationOpen((value) => !value)}
          onMarkNotificationRead={async (notificationId) => {
            const readAt = new Date().toISOString();
            setNotifications((items) => items.map((item) => (
              item.id === notificationId ? { ...item, read_at: item.read_at || readAt } : item
            )));
            await markNotificationRead(notificationId);
            await loadAll(activeSellerId);
          }}
          onMarkAllNotificationsRead={async () => {
            const readAt = new Date().toISOString();
            setNotifications((items) => items.map((item) => ({ ...item, read_at: item.read_at || readAt })));
            if (!notificationFilters.role) {
              return;
            }
            await markAllNotificationsRead({
              role: notificationFilters.role,
              recipient_id: notificationFilters.recipient_id,
            });
            await loadAll(activeSellerId);
          }}
          sessionLabel={session.role === 'seller' ? t(language, 'dashboard.sellerSession') : session.role === 'ops' ? t(language, 'dashboard.opsSession') : t(language, 'dashboard.buyerSession')}
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
              demandPools={demandPools}
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
              onCreateDemand={async (payload) => {
                await reportBuyerDemandSearch({
                  ...payload,
                  buyer_id: session.phone_number || buyerSessionIdRef.current,
                });
                await loadAll(activeSellerId);
              }}
              buyerDemands={buyerDemands}
              buyerDeliveries={buyerDeliveries}
              onPostDemandRequest={async (payload) => {
                await createDemandRequest(payload);
                await loadAll(activeSellerId);
              }}
              onConfirmDelivery={async (deliveryId, qualityIssue, notes) => {
                await confirmBuyerDelivery(deliveryId, {
                  buyer_id: session.phone_number,
                  quality_issue: qualityIssue,
                  notes,
                });
                await loadAll(activeSellerId);
              }}
            />
          ) : session.role === 'seller' ? (
            <SellerWorkspace
              sectionId={sellerSection}
              language={language}
              session={session}
              seller={currentSeller}
              dashboard={dashboard}
              ledger={ledger}
              orders={sectionScopedSellerOrders}
              notifications={sectionScopedSellerNotifications}
              demandPools={demandPools}
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
              commitPools={commitPools}
              listings={listings}
              deliveries={deliveries}
              onCommitPool={async (poolId, listingId, pricePerKg) => {
                await commitToPool(poolId, { seller_id: activeSellerId!, listing_id: listingId, price_per_kg: pricePerKg });
                await loadAll(activeSellerId);
              }}
              onAdvanceDelivery={async (deliveryId, status) => {
                await advanceDelivery(deliveryId, status);
                await loadAll(activeSellerId);
              }}
            />
          ) : (
            <OpsWorkspace
              sectionId={opsSection}
              language={language}
              dashboard={opsDashboard}
              onUpdateQuality={async (listingId, payload) => {
                await updateListingQuality(listingId, payload);
                await loadAll(activeSellerId);
              }}
              onAdvanceDelivery={async (deliveryId, nextStatus) => {
                await advanceDeliveryForActor(deliveryId, {
                  next_status: nextStatus,
                  actor_role: 'ops',
                  actor_id: session.ops_id || session.phone_number,
                });
                await loadAll(activeSellerId);
              }}
            />
          )}
        </DashboardLayout>
      )}

      {selectedListing && session?.role === 'buyer' && (
        <OrderModal
          listing={selectedListing}
          language={language}
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
