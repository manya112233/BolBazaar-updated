import { useMemo } from 'react';
import type { AppLanguage } from '../../App';
import type { AuthSession, Insight, Listing, Notification, Order, SellerDashboard, SellerProfile } from '../../types';
import Filters from '../Filters';
import ListingCard from '../ListingCard';
import ActivityTimeline from './ActivityTimeline';
import { BarAnalytics, ColumnAnalytics } from './AnalyticsPanel';
import DataTable from './DataTable';
import KpiCard from './KpiCard';
import StatusBadge from './StatusBadge';

function averagePrice(listings: Listing[]) {
  if (listings.length === 0) return 0;
  return Math.round(listings.reduce((sum, listing) => sum + listing.price_per_kg, 0) / listings.length);
}

export default function BuyerOverview({
  sectionId,
  language,
  session,
  listings,
  sellers,
  orders,
  notifications,
  dashboard,
  insight,
  selectedSellerId,
  query,
  maxPrice,
  loading,
  onSelectSeller,
  onQueryChange,
  onMaxPriceChange,
  onOrder,
}: {
  sectionId: string;
  language: AppLanguage;
  session: AuthSession;
  listings: Listing[];
  sellers: SellerProfile[];
  orders: Order[];
  notifications: Notification[];
  dashboard: SellerDashboard | null;
  insight: Insight | null;
  selectedSellerId: string | null;
  query: string;
  maxPrice: number;
  loading: boolean;
  onSelectSeller: (sellerId: string) => void;
  onQueryChange: (value: string) => void;
  onMaxPriceChange: (value: number) => void;
  onOrder: (listing: Listing) => void;
}) {
  const acceptedOrders = useMemo(
    () => orders.filter((order) => order.status === 'accepted' || order.status === 'completed'),
    [orders],
  );

  const buyerOrders = useMemo(
    () => orders.filter((order) => order.buyer_name.toLowerCase().includes(session.phone_number.slice(-4))),
    [orders, session.phone_number],
  );

  const spotlightSeller = useMemo(
    () => sellers.find((seller) => seller.seller_id === selectedSellerId) || sellers[0] || null,
    [selectedSellerId, sellers],
  );

  const trustedSellerRows = useMemo(
    () =>
      sellers.map((seller) => ({
        ...seller,
        liveListings: listings.filter((listing) => listing.seller_id === seller.seller_id).length,
        pendingOrders: orders.filter((order) => order.seller_id === seller.seller_id && order.status === 'pending').length,
      })),
    [listings, orders, sellers],
  );

  const stockByProduce = useMemo(() => {
    const buckets = new Map<string, number>();
    for (const listing of listings) {
      buckets.set(listing.product_name, (buckets.get(listing.product_name) || 0) + listing.available_kg);
    }
    return Array.from(buckets.entries()).slice(0, 6).map(([label, value], index) => ({
      label,
      value,
      tone: (['green', 'amber', 'blue', 'slate'] as const)[index % 4],
    }));
  }, [listings]);

  const orderStatus = useMemo(() => {
    const base = [
      { label: 'Pending', value: 0, tone: 'amber' as const },
      { label: 'Accepted', value: 0, tone: 'green' as const },
      { label: 'Rejected', value: 0, tone: 'slate' as const },
      { label: 'Completed', value: 0, tone: 'blue' as const },
    ];
    for (const order of orders) {
      const target = base.find((item) => item.label.toLowerCase() === order.status);
      if (target) target.value += 1;
    }
    return base;
  }, [orders]);

  const recentOrderTrend = useMemo(
    () =>
      acceptedOrders.slice(-6).map((order, index) => ({
        label: `#${index + 1}`,
        value: order.total_price,
        tone: 'blue' as const,
      })),
    [acceptedOrders],
  );

  const activityItems = useMemo(
    () =>
      notifications.slice().reverse().slice(0, 6).map((note) => ({
        title: note.seller_id,
        body: note.text,
        meta: note.order_id,
        tone: note.delivery_status === 'sent' ? 'success' as const : 'neutral' as const,
        badge: note.delivery_status,
      })),
    [notifications],
  );

  const showMarketplace = sectionId === 'marketplace';
  const showOrders = sectionId === 'orders';
  const showSellers = sectionId === 'sellers';
  const showDemand = sectionId === 'demand';

  return (
    <div className="bb-page">
      <section className="bb-page-copy">
        <div>
          <h1>Buyer marketplace dashboard</h1>
          <p>Search live produce, compare trusted sellers, and convert demand into structured orders and seller alerts.</p>
        </div>
        <div className="bb-page-chips">
          <StatusBadge label="Buyer workspace" tone="info" />
          <StatusBadge label={loading ? 'Refreshing' : 'Live marketplace'} tone={loading ? 'warning' : 'success'} dot />
        </div>
      </section>

      <section className="bb-kpi-grid">
        <KpiCard label="Live listings" value={String(listings.length)} meta="Visible produce lots" tone="success" />
        <KpiCard label="Active sellers" value={String(sellers.length)} meta="Phone-linked marketplace suppliers" tone="info" />
        <KpiCard label="Accepted orders" value={String(acceptedOrders.length)} meta="Accepted and completed flow" tone="warning" />
        <KpiCard label="Average price" value={`Rs ${averagePrice(listings)}/kg`} meta={`Buyer ${session.phone_number.slice(-4)}`} tone="neutral" />
      </section>

      <div className="bb-two-column">
        <section className="bb-panel">
          <div className="bb-panel-head">
            <div>
              <h3>Marketplace filters</h3>
              <p>Search produce by seller, pickup area, and price ceiling.</p>
            </div>
          </div>
          <div className="bb-filter-bar">
            <Filters query={query} setQuery={onQueryChange} maxPrice={maxPrice} setMaxPrice={onMaxPriceChange} language={language} />
          </div>
        </section>

        <section className="bb-panel">
          <div className="bb-panel-head">
            <div>
              <h3>Seller spotlight</h3>
              <p>Inspect one seller before placing a fresh order.</p>
            </div>
          </div>
          {spotlightSeller ? (
            <div className="bb-card-stack">
              <label>
                <span className="label">Seller</span>
                <select value={spotlightSeller.seller_id} onChange={(event) => onSelectSeller(event.target.value)}>
                  {sellers.map((seller) => (
                    <option key={seller.seller_id} value={seller.seller_id}>
                      {seller.store_name || seller.seller_name}
                    </option>
                  ))}
                </select>
              </label>
              <div className="bb-summary-grid">
                <div className="summary-box">
                  <div>
                    <span className="label">Pickup default</span>
                    <strong>{dashboard?.default_pickup_location || spotlightSeller.default_pickup_location || 'Not set'}</strong>
                  </div>
                </div>
                <div className="summary-box">
                  <div>
                    <span className="label">Live stock</span>
                    <strong>{dashboard?.total_available_kg || 0} kg</strong>
                  </div>
                </div>
                <div className="summary-box">
                  <div>
                    <span className="label">Pending orders</span>
                    <strong>{dashboard?.pending_orders || 0}</strong>
                  </div>
                </div>
                <div className="summary-box">
                  <div>
                    <span className="label">Repeat buyers</span>
                    <strong>{dashboard?.repeat_customers || 0}</strong>
                  </div>
                </div>
              </div>
              {insight ? (
                <div className="summary-box">
                  <div>
                    <span className="label">AI note</span>
                    <strong>{insight.headline}</strong>
                    <p className="bb-inline-note">{insight.message}</p>
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="bb-empty-state">
              <strong>No sellers available</strong>
              <p>Seller profiles appear here after onboarding and listing activity.</p>
            </div>
          )}
        </section>
      </div>

      {(showMarketplace || showDemand) && (
        <section className="bb-panel">
          <div className="bb-panel-head">
            <div>
              <h3>Marketplace listings</h3>
              <p>Professional buyer grid with AI quality and same-day pickup context.</p>
            </div>
            <StatusBadge label={loading ? 'Refreshing' : 'Live feed'} tone={loading ? 'warning' : 'success'} />
          </div>
          {listings.length > 0 ? (
            <div className="listing-grid">
              {listings.map((listing) => (
                <ListingCard key={listing.id} listing={listing} language={language} onOrder={onOrder} />
              ))}
            </div>
          ) : (
            <div className="bb-empty-state">
              <strong>No marketplace matches</strong>
              <p>Adjust the current query or max price to widen the market view.</p>
            </div>
          )}
        </section>
      )}

      <div className="bb-two-column">
        {(showMarketplace || showOrders) && (
          <section className="bb-panel">
            <div className="bb-panel-head">
              <div>
                <h3>Buyer orders</h3>
                <p>Structured order queue with seller and pickup context.</p>
              </div>
            </div>
            <DataTable
              columns={[
                { key: 'produce', label: 'Produce', render: (row: Order) => <strong>{row.product_name}</strong> },
                { key: 'seller', label: 'Seller', render: (row: Order) => row.seller_name },
                { key: 'qty', label: 'Qty', align: 'right', render: (row: Order) => `${row.quantity_kg} kg` },
                { key: 'pickup', label: 'Pickup', render: (row: Order) => row.pickup_time },
                {
                  key: 'status',
                  label: 'Status',
                  render: (row: Order) => <StatusBadge label={row.status} tone={row.status === 'accepted' || row.status === 'completed' ? 'success' : row.status === 'pending' ? 'warning' : 'neutral'} />,
                },
                { key: 'value', label: 'Value', align: 'right', render: (row: Order) => `Rs ${row.total_price}` },
              ]}
              rows={buyerOrders}
              emptyTitle="No buyer orders yet"
              emptyBody="Place a marketplace order to start your buyer activity queue."
            />
          </section>
        )}

        {(showMarketplace || showSellers) && (
          <section className="bb-panel">
            <div className="bb-panel-head">
              <div>
                <h3>Trusted sellers</h3>
                <p>Compact seller table with live listing and pending order signals.</p>
              </div>
            </div>
            <DataTable
              columns={[
                { key: 'seller', label: 'Seller', render: (row: SellerProfile & { liveListings: number; pendingOrders: number }) => <strong>{row.store_name || row.seller_name}</strong> },
                { key: 'type', label: 'Type', render: (row: SellerProfile) => row.seller_type || 'Not set' },
                { key: 'pickup', label: 'Pickup', render: (row: SellerProfile) => row.default_pickup_location || 'Not set' },
                { key: 'lots', label: 'Listings', align: 'right', render: (row: SellerProfile & { liveListings: number }) => row.liveListings },
                { key: 'pending', label: 'Pending', align: 'right', render: (row: SellerProfile & { pendingOrders: number }) => row.pendingOrders },
                { key: 'status', label: 'Trust', render: () => <StatusBadge label="Trusted" tone="success" /> },
              ]}
              rows={trustedSellerRows}
              emptyTitle="No sellers available"
              emptyBody="Seller profiles will appear after onboarding and live listings."
            />
          </section>
        )}
      </div>

      {(showMarketplace || showDemand || showOrders) && (
        <section className="bb-analytics-grid">
          <BarAnalytics title="Orders by status" subtitle="Buyer-side execution mix." items={orderStatus} />
          <BarAnalytics title="Available stock by produce" subtitle="Current open supply by produce." items={stockByProduce} formatValue={(value) => `${value} kg`} />
          <ColumnAnalytics title="Accepted order value trend" subtitle="Recent accepted order values." items={recentOrderTrend} formatValue={(value) => `Rs ${value}`} />
          <section className="bb-panel">
            <div className="bb-panel-head">
              <div>
                <h3>Demand signals</h3>
                <p>Buyer searches can trigger seller alerts for fast-moving produce.</p>
              </div>
            </div>
            <ActivityTimeline
              items={activityItems}
              emptyTitle="No seller alerts yet"
              emptyBody="Demand pushes, listing confirmations, and seller responses will appear here."
            />
          </section>
        </section>
      )}
    </div>
  );
}
