import type { Insight, Notification, Order, SellerDashboard, SellerLedgerView, SellerProfile } from '../types';

export default function StatusPanel({
  sellers,
  selectedSellerId,
  onSelectSeller,
  dashboard,
  ledger,
  orders,
  notifications,
  insight,
  onRespondOrder,
}: {
  sellers: SellerProfile[];
  selectedSellerId: string | null;
  onSelectSeller: (sellerId: string) => void;
  dashboard: SellerDashboard | null;
  ledger: SellerLedgerView | null;
  orders: Order[];
  notifications: Notification[];
  insight: Insight | null;
  onRespondOrder: (orderId: string, decision: 'accept' | 'reject') => Promise<void>;
}) {
  const visibleOrders = orders
    .filter((order) => (selectedSellerId ? order.seller_id === selectedSellerId : true))
    .slice()
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return (
    <div className="status-panel">
      <section className="card">
        <div className="panel-header">
          <div>
            <h3>Seller control center</h3>
            <p className="muted compact">Profile, location, live inventory, and daily business stats from the registered WhatsApp seller.</p>
          </div>
          {sellers.length > 0 && (
            <label className="seller-selector">
              <span className="label">Seller</span>
              <select value={selectedSellerId || ''} onChange={(event) => onSelectSeller(event.target.value)}>
                {sellers.map((seller) => (
                  <option key={seller.seller_id} value={seller.seller_id}>
                    {seller.store_name || seller.seller_name}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>

        {dashboard ? (
          <>
            <div className="details-grid">
              <div>
                <span className="label">Store</span>
                <strong>{dashboard.store_name || dashboard.seller_name}</strong>
              </div>
              <div>
                <span className="label">Language</span>
                <strong>{dashboard.preferred_language === 'hi' ? 'Hindi' : 'English'}</strong>
              </div>
              <div>
                <span className="label">Pickup</span>
                <strong>{dashboard.default_pickup_location || 'Not set'}</strong>
              </div>
              <div>
                <span className="label">Live listings</span>
                <strong>{dashboard.live_listings_count}</strong>
              </div>
            </div>

            <div className="metric-grid">
              <div className="metric-tile">
                <span className="label">Available stock</span>
                <strong>{dashboard.total_available_kg} kg</strong>
              </div>
              <div className="metric-tile">
                <span className="label">Sold today</span>
                <strong>{dashboard.sold_today_kg} kg</strong>
              </div>
              <div className="metric-tile">
                <span className="label">Revenue today</span>
                <strong>Rs {dashboard.sold_today_revenue}</strong>
              </div>
              <div className="metric-tile">
                <span className="label">Customers</span>
                <strong>{dashboard.total_customers}</strong>
              </div>
              <div className="metric-tile">
                <span className="label">Repeat buyers</span>
                <strong>{dashboard.repeat_customers}</strong>
              </div>
              <div className="metric-tile">
                <span className="label">Pending orders</span>
                <strong>{dashboard.pending_orders}</strong>
              </div>
              <div className="metric-tile">
                <span className="label">Khata entries</span>
                <strong>{dashboard.ledger_entries_count}</strong>
              </div>
              <div className="metric-tile">
                <span className="label">Outstanding dues</span>
                <strong>Rs {dashboard.ledger_outstanding_amount}</strong>
              </div>
            </div>
          </>
        ) : (
          <p className="muted">No seller profile has completed WhatsApp registration yet.</p>
        )}
      </section>

      <section className="card">
        <div className="panel-header">
          <div>
            <h3>Smart voice ledger</h3>
            <p className="muted compact">Voice or text khata notes from WhatsApp become seller-side credit and payment records.</p>
          </div>
        </div>
        {!ledger || ledger.summary.total_entries === 0 ? (
          <p className="muted">No khata records yet. A farmer can send a note like “Raju bought 10 kg tomatoes for Rs 250 and still owes Rs 50.”</p>
        ) : (
          <>
            <div className="metric-grid compact-grid">
              <div className="metric-tile">
                <span className="label">Entries</span>
                <strong>{ledger.summary.total_entries}</strong>
              </div>
              <div className="metric-tile">
                <span className="label">Outstanding</span>
                <strong>Rs {ledger.summary.total_outstanding_amount}</strong>
              </div>
              <div className="metric-tile">
                <span className="label">Collected</span>
                <strong>Rs {ledger.summary.total_collected_amount}</strong>
              </div>
              <div className="metric-tile">
                <span className="label">Buyers with dues</span>
                <strong>{ledger.summary.buyers_with_balance}</strong>
              </div>
            </div>

            <ul className="stack-list ledger-list">
              {ledger.items.slice(0, 6).map((entry) => (
                <li key={entry.id}>
                  <div className="pill-row">
                    <strong>{entry.buyer_name}</strong>
                    <span className={`mini-pill ${entry.entry_kind === 'payment' ? 'success-pill' : 'neutral-pill'}`}>
                      {entry.entry_kind === 'payment' ? 'Payment' : 'Sale'}
                    </span>
                    <span className="mini-pill">{entry.capture_mode === 'voice_note' ? 'Voice note' : 'Text note'}</span>
                  </div>
                  <p>{entry.summary}</p>
                  <p>
                    {entry.entry_kind === 'payment'
                      ? `Received Rs ${entry.amount_paid}`
                      : `Total Rs ${entry.total_amount || 0} | Paid Rs ${entry.amount_paid} | Due Rs ${entry.amount_due}`}
                  </p>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className="card">
        <div className="panel-header">
          <div>
            <h3>Recent customers</h3>
            <p className="muted compact">Accepted buyers for the selected seller.</p>
          </div>
        </div>
        {!dashboard || dashboard.recent_customers.length === 0 ? (
          <p className="muted">No customer names yet.</p>
        ) : (
          <ul className="stack-list">
            {dashboard.recent_customers.map((customer) => (
              <li key={customer}>
                <strong>{customer}</strong>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <div className="panel-header">
          <div>
            <h3>Recent orders</h3>
            <p className="muted compact">Item, buyer, pickup time, and seller decision.</p>
          </div>
        </div>
        {visibleOrders.length === 0 ? (
          <p className="muted">No orders for this seller yet.</p>
        ) : (
          <ul className="stack-list order-list">
            {visibleOrders.map((order) => (
              <li key={order.id}>
                <div className="pill-row">
                  <strong>{order.product_name || 'Items'}</strong>
                  <span className={`mini-pill status-${order.status}`}>{order.status}</span>
                </div>
                <p>
                  {order.quantity_kg} kg for {order.buyer_name}
                </p>
                <p>
                  Pickup {order.pickup_time} | Rs {order.total_price}
                </p>
                {order.status === 'pending' && (
                  <div className="action-cluster order-actions">
                    <button className="primary-button small" onClick={() => void onRespondOrder(order.id, 'accept')}>
                      Accept
                    </button>
                    <button className="ghost-button small" onClick={() => void onRespondOrder(order.id, 'reject')}>
                      Reject
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <h3>Seller alerts</h3>
        {notifications.length === 0 ? (
          <p className="muted">No seller alerts yet.</p>
        ) : (
          <ul className="stack-list">
            {notifications
              .filter((note) => (selectedSellerId ? note.seller_id === selectedSellerId : true))
              .slice()
              .reverse()
              .slice(0, 3)
              .map((note) => (
                <li key={`${note.order_id}-${note.seller_id}`}>
                  <div className="pill-row">
                    <strong>{note.order_id}</strong>
                    <span className="mini-pill">{note.delivery_status}</span>
                  </div>
                  <p>{note.text}</p>
                </li>
              ))}
          </ul>
        )}
      </section>

      <section className="card highlight">
        <h3>AI seller copilot</h3>
        {insight ? (
          <>
            <strong>{insight.headline}</strong>
            <p>{insight.message}</p>
          </>
        ) : (
          <p className="muted">Accept an order to generate the first seller insight.</p>
        )}
      </section>
    </div>
  );
}
