import { useMemo, useState, type FormEvent } from 'react';
import type { AppLanguage } from '../../App';
import type { AuthSession, Insight, Notification, Order, SellerDashboard, SellerLedgerView, SellerProfile } from '../../types';
import ActivityTimeline from './ActivityTimeline';
import { BarAnalytics, ColumnAnalytics } from './AnalyticsPanel';
import DataTable from './DataTable';
import KpiCard from './KpiCard';
import StatusBadge from './StatusBadge';

type SellerSectionId = 'overview' | 'listings' | 'orders' | 'ledger' | 'insights' | 'profile';

export default function SellerOverview({
  sectionId,
  language,
  session,
  seller,
  dashboard,
  ledger,
  orders,
  notifications,
  insight,
  loading,
  onRespondOrder,
  onRecordLedgerPayment,
}: {
  sectionId: string;
  language: AppLanguage;
  session: AuthSession;
  seller: SellerProfile | null;
  dashboard: SellerDashboard | null;
  ledger: SellerLedgerView | null;
  orders: Order[];
  notifications: Notification[];
  insight: Insight | null;
  loading: boolean;
  onRespondOrder: (orderId: string, decision: 'accept' | 'reject') => Promise<void>;
  onRecordLedgerPayment: (payload: { buyer_name: string; amount_paid: number; notes?: string }) => Promise<void>;
}) {
  const [paymentBuyerName, setPaymentBuyerName] = useState('');
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentNotes, setPaymentNotes] = useState('');
  const [paymentSaving, setPaymentSaving] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);

  const visibleOrders = useMemo(
    () => orders.slice().sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [orders],
  );

  const pendingOrders = visibleOrders.filter((order) => order.status === 'pending');
  const liveListings = dashboard?.recent_listings || [];
  const lowStockCount = liveListings.filter((listing) => listing.available_kg > 0 && listing.available_kg <= 10).length;
  const soldOutCount = liveListings.filter((listing) => listing.available_kg === 0 || listing.status === 'sold_out').length;

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

  const stockByProduce = useMemo(() => {
    const buckets = new Map<string, number>();
    for (const listing of liveListings) {
      buckets.set(listing.product_name, (buckets.get(listing.product_name) || 0) + listing.available_kg);
    }
    return Array.from(buckets.entries()).map(([label, value], index) => ({
      label,
      value,
      tone: (['green', 'amber', 'blue', 'slate'] as const)[index % 4],
    }));
  }, [liveListings]);

  const acceptedTrend = useMemo(
    () =>
      visibleOrders
        .filter((order) => order.status === 'accepted' || order.status === 'completed')
        .slice(0, 6)
        .reverse()
        .map((order, index) => ({
          label: `#${index + 1}`,
          value: order.total_price,
          tone: 'green' as const,
        })),
    [visibleOrders],
  );

  const duesByBuyer = useMemo(() => {
    const balances = new Map<string, number>();
    for (const entry of ledger?.items || []) {
      balances.set(entry.buyer_name, Math.round(((balances.get(entry.buyer_name) || 0) + entry.balance_delta) * 100) / 100);
    }
    return Array.from(balances.entries())
      .filter(([, value]) => value > 0)
      .map(([label, value]) => ({ label, value, tone: 'amber' as const }));
  }, [ledger]);

  const notificationCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const note of notifications) {
      counts.set(note.delivery_status, (counts.get(note.delivery_status) || 0) + 1);
    }
    return Array.from(counts.entries()).map(([label, value], index) => ({
      label,
      value,
      tone: (['green', 'amber', 'blue', 'slate'] as const)[index % 4],
    }));
  }, [notifications]);

  const timelineItems = useMemo(
    () =>
      notifications.slice().reverse().slice(0, 6).map((note) => ({
        title: note.order_id,
        body: note.text,
        meta: note.seller_id,
        tone: note.delivery_status === 'sent' ? 'success' as const : 'neutral' as const,
        badge: note.delivery_status,
      })),
    [notifications],
  );

  const currentSection = (['overview', 'listings', 'orders', 'ledger', 'insights', 'profile'].includes(sectionId)
    ? sectionId
    : 'overview') as SellerSectionId;

  const pageMeta: Record<SellerSectionId, { title: string; body: string }> = {
    overview: {
      title: 'Seller operating dashboard',
      body: 'Track listings, incoming orders, khata balances, AI insights, and WhatsApp activity from one operational console.',
    },
    listings: {
      title: 'Live listings',
      body: 'Monitor buyer-visible inventory, pricing, stock status, and freshness signals.',
    },
    orders: {
      title: 'Orders queue',
      body: 'Review incoming buyer requests and take accept or reject actions quickly.',
    },
    ledger: {
      title: 'Khata ledger',
      body: 'Track dues, collections, and recent ledger entries mapped to this seller.',
    },
    insights: {
      title: 'AI insights',
      body: 'Review seller recommendations, order performance, and WhatsApp activity signals.',
    },
    profile: {
      title: 'Verification and profile',
      body: 'Use the same seller identity across WhatsApp and the web dashboard.',
    },
  };

  const handleLedgerPaymentSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const amount = Number(paymentAmount);
    if (!paymentBuyerName.trim() || !Number.isFinite(amount) || amount <= 0) {
      setPaymentError('Enter buyer name and a valid payment amount.');
      return;
    }

    setPaymentSaving(true);
    setPaymentError(null);
    try {
      await onRecordLedgerPayment({
        buyer_name: paymentBuyerName.trim(),
        amount_paid: amount,
        notes: paymentNotes.trim() || undefined,
      });
      setPaymentBuyerName('');
      setPaymentAmount('');
      setPaymentNotes('');
    } catch (error) {
      setPaymentError(error instanceof Error ? error.message : 'Could not update khata.');
    } finally {
      setPaymentSaving(false);
    }
  };

  const overviewView = (
    <>
      {dashboard ? (
        <>
          <section className="bb-kpi-grid">
            <KpiCard label="Live listings" value={String(dashboard.live_listings_count)} meta="Buyer-visible lots" tone="success" />
            <KpiCard label="Available stock" value={`${dashboard.total_available_kg} kg`} meta="Ready for pickup" tone="info" />
            <KpiCard label="Revenue today" value={`Rs ${dashboard.sold_today_revenue}`} meta={`${dashboard.sold_today_kg} kg sold today`} tone="warning" />
            <KpiCard label="Pending orders" value={String(dashboard.pending_orders)} meta="Needs seller response" tone="warning" />
            <KpiCard label="Outstanding khata" value={`Rs ${dashboard.ledger_outstanding_amount}`} meta={`${dashboard.ledger_buyers_with_balance} buyers with dues`} tone="danger" />
            <KpiCard label="Collected amount" value={`Rs ${dashboard.ledger_collected_amount}`} meta="Recorded collections" tone="success" />
            <KpiCard label="Repeat buyers" value={String(dashboard.repeat_customers)} meta={`${dashboard.total_customers} buyers served`} tone="info" />
            <KpiCard label="Buyers with dues" value={String(dashboard.ledger_buyers_with_balance)} meta="Collection follow-up queue" tone="neutral" />
          </section>

          <div className="bb-three-column">
            <section className="bb-panel">
              <div className="bb-panel-head">
                <div>
                  <h3>Inventory status</h3>
                  <p>Low-stock and sold-out indicators across recent lots.</p>
                </div>
              </div>
              <div className="bb-summary-grid">
                <div className="summary-box"><div><span className="label">Store</span><strong>{seller?.store_name || seller?.seller_name || 'Seller profile'}</strong></div></div>
                <div className="summary-box"><div><span className="label">Pickup</span><strong>{seller?.default_pickup_location || 'Not set'}</strong></div></div>
                <div className="summary-box"><div><span className="label">Low stock</span><strong>{lowStockCount}</strong></div></div>
                <div className="summary-box"><div><span className="label">Sold out</span><strong>{soldOutCount}</strong></div></div>
              </div>
            </section>

            <section className="bb-panel">
              <div className="bb-panel-head">
                <div>
                  <h3>AI seller insight</h3>
                  <p>Signals computed from order conversion, inventory balance, and collections.</p>
                </div>
              </div>
              {insight ? (
                <div className="summary-box">
                  <div>
                    <span className="label">Insight</span>
                    <strong>{insight.headline}</strong>
                    <p className="bb-inline-note">{insight.message}</p>
                  </div>
                </div>
              ) : (
                <div className="bb-empty-state">
                  <strong>Insight warming up</strong>
                  <p>Accept more orders or publish fresh listings to surface the next recommendation.</p>
                </div>
              )}
            </section>

            <section className="bb-panel">
              <div className="bb-panel-head">
                <div>
                  <h3>Verification profile</h3>
                  <p>The same identity is used in WhatsApp and on the dashboard.</p>
                </div>
              </div>
              {seller ? (
                <div className="bb-card-stack">
                  <div className="summary-box"><div><span className="label">Seller type</span><strong>{seller.seller_type || 'Not set'}</strong></div></div>
                  <div className="summary-box"><div><span className="label">Verification method</span><strong>{seller.verification_method || 'Not set'}</strong></div></div>
                  <div className="summary-box"><div><span className="label">Session phone</span><strong>{session.phone_number}</strong></div></div>
                </div>
              ) : (
                <div className="bb-empty-state">
                  <strong>Seller profile missing</strong>
                  <p>Complete onboarding before verification data can be displayed.</p>
                </div>
              )}
            </section>
          </div>

          <div className="bb-two-column">
            <section className="bb-panel">
              <div className="bb-panel-head">
                <div>
                  <h3>Recent orders queue</h3>
                  <p>Accept or reject fresh buyer requests directly from the dashboard.</p>
                </div>
              </div>
              <DataTable
                columns={[
                  { key: 'produce', label: 'Produce', render: (row: Order) => <strong>{row.product_name}</strong> },
                  { key: 'buyer', label: 'Buyer', render: (row: Order) => row.buyer_name },
                  { key: 'qty', label: 'Qty', align: 'right', render: (row: Order) => `${row.quantity_kg} kg` },
                  { key: 'pickup', label: 'Pickup', render: (row: Order) => row.pickup_time },
                  {
                    key: 'status',
                    label: 'Status',
                    render: (row: Order) => <StatusBadge label={row.status} tone={row.status === 'accepted' || row.status === 'completed' ? 'success' : row.status === 'pending' ? 'warning' : 'neutral'} />,
                  },
                  {
                    key: 'actions',
                    label: 'Action',
                    render: (row: Order) =>
                      row.status === 'pending' ? (
                        <div className="action-row">
                          <button className="primary-button small" onClick={() => void onRespondOrder(row.id, 'accept')}>Accept</button>
                          <button className="ghost-button small" onClick={() => void onRespondOrder(row.id, 'reject')}>Reject</button>
                        </div>
                      ) : (
                        <span className="bb-inline-note">Closed</span>
                      ),
                  },
                ]}
                rows={visibleOrders}
                emptyTitle="No orders yet"
                emptyBody="Buyer orders will appear here as soon as marketplace demand converts."
              />
            </section>

            <section className="bb-panel">
              <div className="bb-panel-head">
                <div>
                  <h3>Recent live listings</h3>
                  <p>Inventory snapshot with stock and freshness status.</p>
                </div>
              </div>
              <DataTable
                columns={[
                  { key: 'produce', label: 'Produce', render: (row: SellerDashboard['recent_listings'][number]) => <strong>{row.product_name}</strong> },
                  { key: 'pickup', label: 'Pickup', render: (row) => row.pickup_location },
                  { key: 'stock', label: 'Stock', align: 'right', render: (row) => `${row.available_kg} kg` },
                  { key: 'price', label: 'Price', align: 'right', render: (row) => `Rs ${row.price_per_kg}` },
                  {
                    key: 'state',
                    label: 'State',
                    render: (row) =>
                      row.available_kg === 0 || row.status === 'sold_out' ? (
                        <StatusBadge label="Sold out" tone="danger" />
                      ) : row.available_kg <= 10 ? (
                        <StatusBadge label="Low stock" tone="warning" />
                      ) : (
                        <StatusBadge label="Live" tone="success" />
                      ),
                  },
                ]}
                rows={liveListings.slice(0, 6)}
                emptyTitle="No live listings yet"
                emptyBody="Create or confirm a listing through WhatsApp to populate this table."
              />
            </section>
          </div>

          <div className="bb-two-column">
            <section className="bb-panel">
              <div className="bb-panel-head">
                <div>
                  <h3>WhatsApp activity timeline</h3>
                  <p>Notifications, demand pushes, and order prompts sent to the linked seller number.</p>
                </div>
              </div>
              <ActivityTimeline
                items={timelineItems}
                emptyTitle="No alerts yet"
                emptyBody="Order prompts, demand pushes, and listing confirmations will appear here."
              />
            </section>

            <section className="bb-panel">
              <div className="bb-panel-head">
                <div>
                  <h3>Khata snapshot</h3>
                  <p>Outstanding balances and recent payment movement.</p>
                </div>
              </div>
              {ledger ? (
                <>
                  <p className="bb-table-card-caption">
                    Outstanding Rs {ledger.summary.total_outstanding_amount} across {ledger.summary.buyers_with_balance} buyers. Collected Rs {ledger.summary.total_collected_amount}.
                  </p>
                  <DataTable
                    columns={[
                      { key: 'buyer', label: 'Buyer', render: (row: SellerLedgerView['items'][number]) => <strong>{row.buyer_name}</strong> },
                      { key: 'kind', label: 'Entry', render: (row) => <StatusBadge label={row.entry_kind === 'payment' ? 'Payment' : 'Sale'} tone={row.entry_kind === 'payment' ? 'success' : 'info'} /> },
                      { key: 'summary', label: 'Summary', render: (row) => row.summary },
                      { key: 'delta', label: 'Balance', align: 'right', render: (row) => `Rs ${Math.round(row.balance_delta)}` },
                    ]}
                    rows={ledger.items.slice(0, 5)}
                    emptyTitle="No khata records yet"
                    emptyBody="Voice notes and text notes from WhatsApp will create ledger entries here."
                  />
                </>
              ) : (
                <div className="bb-empty-state">
                  <strong>No khata records yet</strong>
                  <p>WhatsApp credit notes and payment notes will surface here.</p>
                </div>
              )}
            </section>
          </div>

          <section className="bb-analytics-grid">
            <BarAnalytics title="Orders by status" subtitle="Operational queue mix." items={orderStatus} />
            <BarAnalytics title="Available stock by produce" subtitle="Open supply by produce type." items={stockByProduce} formatValue={(value) => `${value} kg`} />
            <ColumnAnalytics title="Revenue trend" subtitle="Recent accepted and completed order value." items={acceptedTrend} formatValue={(value) => `Rs ${value}`} />
            <BarAnalytics title="Khata outstanding by buyer" subtitle="Highest open balances." items={duesByBuyer.slice(0, 6)} formatValue={(value) => `Rs ${value}`} />
            <BarAnalytics title="WhatsApp activity count" subtitle="Notification delivery activity." items={notificationCounts} />
          </section>
        </>
      ) : (
        <div className="bb-empty-state">
          <strong>Seller profile not ready yet</strong>
          <p>Complete WhatsApp onboarding and publish a live listing to unlock the full dashboard.</p>
        </div>
      )}
    </>
  );

  const listingsView = (
    <section className="bb-panel">
      <div className="bb-panel-head">
        <div>
          <h3>Seller live listings</h3>
          <p>All current lots with stock, pricing, pickup, freshness, and status context.</p>
        </div>
      </div>
      <DataTable
        columns={[
          { key: 'produce', label: 'Produce', render: (row: SellerDashboard['recent_listings'][number]) => <strong>{row.product_name}</strong> },
          { key: 'pickup', label: 'Pickup', render: (row) => row.pickup_location },
          { key: 'stock', label: 'Stock', align: 'right', render: (row) => `${row.available_kg} kg` },
          { key: 'price', label: 'Price', align: 'right', render: (row) => `Rs ${row.price_per_kg}` },
          { key: 'freshness', label: 'Freshness', render: (row) => row.freshness_label },
          {
            key: 'quality',
            label: 'Quality',
            render: (row) => row.quality_assessment_source === 'ai_visual' ? <StatusBadge label="AI checked" tone="success" /> : <StatusBadge label="Text signal" tone="neutral" />,
          },
          {
            key: 'state',
            label: 'State',
            render: (row) =>
              row.available_kg === 0 || row.status === 'sold_out' ? (
                <StatusBadge label="Sold out" tone="danger" />
              ) : row.available_kg <= 10 ? (
                <StatusBadge label="Low stock" tone="warning" />
              ) : (
                <StatusBadge label="Live" tone="success" />
              ),
          },
        ]}
        rows={liveListings}
        emptyTitle="No live listings yet"
        emptyBody="Create or confirm a listing through WhatsApp to populate this table."
      />
    </section>
  );

  const ordersView = (
    <div className="bb-two-column">
      <section className="bb-panel">
        <div className="bb-panel-head">
          <div>
            <h3>Orders queue</h3>
            <p>Review every buyer order and respond from the dashboard.</p>
          </div>
        </div>
        <DataTable
          columns={[
            { key: 'produce', label: 'Produce', render: (row: Order) => <strong>{row.product_name}</strong> },
            { key: 'buyer', label: 'Buyer', render: (row: Order) => row.buyer_name },
            { key: 'qty', label: 'Qty', align: 'right', render: (row: Order) => `${row.quantity_kg} kg` },
            { key: 'pickup', label: 'Pickup', render: (row: Order) => row.pickup_time },
            { key: 'value', label: 'Value', align: 'right', render: (row: Order) => `Rs ${row.total_price}` },
            {
              key: 'status',
              label: 'Status',
              render: (row: Order) => <StatusBadge label={row.status} tone={row.status === 'accepted' || row.status === 'completed' ? 'success' : row.status === 'pending' ? 'warning' : 'neutral'} />,
            },
            {
              key: 'actions',
              label: 'Action',
              render: (row: Order) =>
                row.status === 'pending' ? (
                  <div className="action-row">
                    <button className="primary-button small" onClick={() => void onRespondOrder(row.id, 'accept')}>Accept</button>
                    <button className="ghost-button small" onClick={() => void onRespondOrder(row.id, 'reject')}>Reject</button>
                  </div>
                ) : (
                  <span className="bb-inline-note">Closed</span>
                ),
            },
          ]}
          rows={visibleOrders}
          emptyTitle="No orders yet"
          emptyBody="Buyer orders will appear here as soon as marketplace demand converts."
        />
      </section>

      <section className="bb-panel">
        <div className="bb-panel-head">
          <div>
            <h3>Order analytics</h3>
            <p>Execution mix and recent accepted order value.</p>
          </div>
        </div>
        <BarAnalytics title="Orders by status" subtitle="Current queue mix." items={orderStatus} />
        <div style={{ height: 16 }} />
        <ColumnAnalytics title="Recent accepted value" subtitle="Accepted and completed order value." items={acceptedTrend} formatValue={(value) => `Rs ${value}`} />
      </section>
    </div>
  );

  const ledgerView = (
    <div className="bb-two-column">
      <section className="bb-panel">
        <div className="bb-panel-head">
          <div>
            <h3>Khata ledger</h3>
            <p>Recent entries, outstanding balances, and payment capture.</p>
          </div>
        </div>

        <form className="ledger-payment-form" onSubmit={handleLedgerPaymentSubmit}>
          <div>
            <label className="label">Buyer name</label>
            <input value={paymentBuyerName} onChange={(event) => setPaymentBuyerName(event.target.value)} placeholder="Raju" />
          </div>
          <div>
            <label className="label">Amount paid</label>
            <input type="number" min="1" step="1" value={paymentAmount} onChange={(event) => setPaymentAmount(event.target.value)} placeholder="500" />
          </div>
          <div className="ledger-payment-notes">
            <label className="label">Note</label>
            <input value={paymentNotes} onChange={(event) => setPaymentNotes(event.target.value)} placeholder="UPI, cash, part payment..." />
          </div>
          <button className="primary-button" type="submit" disabled={paymentSaving}>
            {paymentSaving ? 'Updating...' : 'Record payment'}
          </button>
          {paymentError ? <p className="error-text">{paymentError}</p> : null}
        </form>

        {ledger ? (
          <>
            <p className="bb-table-card-caption">
              Outstanding Rs {ledger.summary.total_outstanding_amount} across {ledger.summary.buyers_with_balance} buyers. Collected Rs {ledger.summary.total_collected_amount}.
            </p>
            <DataTable
              columns={[
                { key: 'buyer', label: 'Buyer', render: (row: SellerLedgerView['items'][number]) => <strong>{row.buyer_name}</strong> },
                { key: 'kind', label: 'Entry', render: (row) => <StatusBadge label={row.entry_kind === 'payment' ? 'Payment' : 'Sale'} tone={row.entry_kind === 'payment' ? 'success' : 'info'} /> },
                { key: 'capture', label: 'Source', render: (row) => row.capture_mode === 'voice_note' ? 'Voice note' : 'Text note' },
                { key: 'summary', label: 'Summary', render: (row) => row.summary },
                { key: 'delta', label: 'Balance', align: 'right', render: (row) => `Rs ${Math.round(row.balance_delta)}` },
              ]}
              rows={ledger.items}
              emptyTitle="No khata records yet"
              emptyBody="Voice notes and text notes from WhatsApp will create ledger entries here."
            />
          </>
        ) : (
          <div className="bb-empty-state">
            <strong>No khata records yet</strong>
            <p>WhatsApp credit notes and payment notes will surface here.</p>
          </div>
        )}
      </section>

      <section className="bb-panel">
        <div className="bb-panel-head">
          <div>
            <h3>Ledger analytics</h3>
            <p>Collection priorities across the current khata book.</p>
          </div>
        </div>
        <BarAnalytics title="Khata outstanding by buyer" subtitle="Highest open balances." items={duesByBuyer.slice(0, 6)} formatValue={(value) => `Rs ${value}`} />
      </section>
    </div>
  );

  const insightsView = (
    <div className="bb-two-column">
      <section className="bb-panel">
        <div className="bb-panel-head">
          <div>
            <h3>AI seller insight</h3>
            <p>Seller recommendations from orders, inventory, and collections.</p>
          </div>
        </div>
        {insight ? (
          <div className="summary-box">
            <div>
              <span className="label">Insight</span>
              <strong>{insight.headline}</strong>
              <p className="bb-inline-note">{insight.message}</p>
            </div>
          </div>
        ) : (
          <div className="bb-empty-state">
            <strong>Insight warming up</strong>
            <p>Accept more orders or publish fresh listings to surface the next recommendation.</p>
          </div>
        )}
        <div style={{ height: 16 }} />
        <BarAnalytics title="WhatsApp activity count" subtitle="Notification delivery activity." items={notificationCounts} />
      </section>

      <section className="bb-panel">
        <div className="bb-panel-head">
          <div>
            <h3>WhatsApp activity timeline</h3>
            <p>Notifications, demand pushes, and order prompts sent to the linked seller number.</p>
          </div>
        </div>
        <ActivityTimeline
          items={timelineItems}
          emptyTitle="No alerts yet"
          emptyBody="Order prompts, demand pushes, and listing confirmations will appear here."
        />
      </section>
    </div>
  );

  const profileView = (
    <section className="bb-panel">
      <div className="bb-panel-head">
        <div>
          <h3>Verification profile</h3>
          <p>The same identity is used in WhatsApp and on the dashboard.</p>
        </div>
      </div>
      {seller ? (
        <div className="bb-three-column">
          <div className="summary-box"><div><span className="label">Seller name</span><strong>{seller.seller_name}</strong></div></div>
          <div className="summary-box"><div><span className="label">Store name</span><strong>{seller.store_name || 'Not set'}</strong></div></div>
          <div className="summary-box"><div><span className="label">Seller type</span><strong>{seller.seller_type || 'Not set'}</strong></div></div>
          <div className="summary-box"><div><span className="label">Verification</span><strong>{seller.verification_status || 'unverified'}</strong></div></div>
          <div className="summary-box"><div><span className="label">Method</span><strong>{seller.verification_method || 'Not set'}</strong></div></div>
          <div className="summary-box"><div><span className="label">Session phone</span><strong>{session.phone_number}</strong></div></div>
        </div>
      ) : (
        <div className="bb-empty-state">
          <strong>Seller profile missing</strong>
          <p>Complete onboarding before verification data can be displayed.</p>
        </div>
      )}
    </section>
  );

  const sectionView: Record<SellerSectionId, JSX.Element> = {
    overview: overviewView,
    listings: listingsView,
    orders: ordersView,
    ledger: ledgerView,
    insights: insightsView,
    profile: profileView,
  };

  return (
    <div className="bb-page">
      <section className="bb-page-copy">
        <div>
          <h1>{pageMeta[currentSection].title}</h1>
          <p>{pageMeta[currentSection].body}</p>
        </div>
        <div className="bb-page-chips">
          <StatusBadge label={seller?.verification_status || 'unverified'} tone={seller?.verification_status === 'verified' ? 'success' : 'warning'} />
          <StatusBadge label={`${pendingOrders.length} pending orders`} tone="warning" dot={pendingOrders.length > 0} />
          <StatusBadge label={loading ? 'Refreshing' : 'Sync active'} tone={loading ? 'info' : 'success'} dot />
        </div>
      </section>

      {sectionView[currentSection]}
    </div>
  );
}
