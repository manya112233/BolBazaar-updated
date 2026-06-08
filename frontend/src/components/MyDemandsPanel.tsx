import type { DemandRequest, Delivery } from '../types';

type MyDemandsPanelProps = {
  demands: DemandRequest[];
  deliveries: Delivery[];
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
  } catch {
    return iso;
  }
}

export default function MyDemandsPanel({ demands, deliveries }: MyDemandsPanelProps) {
  const deliveriesByBuyer = deliveries;

  return (
    <div className="demands-panel slide-in">
      <h3>📦 My Demands & Deliveries</h3>

      {demands.length === 0 && deliveriesByBuyer.length === 0 && (
        <div className="empty-state card">
          <div className="empty-icon">📋</div>
          <strong>No demands yet</strong>
          <p>Post a demand request and sellers will find you!</p>
        </div>
      )}

      {demands.length > 0 && (
        <>
          <p className="muted" style={{ margin: '0 0 8px', fontSize: '0.88rem' }}>
            {demands.length} demand{demands.length !== 1 ? 's' : ''} posted
          </p>
          {demands.map((d) => (
            <div key={d.id} className="demand-card card">
              <div className="demand-card-header">
                <h4>{d.product_name}</h4>
                <span className={`status-pill status-${d.status}`}>{d.status}</span>
              </div>
              <div className="demand-card-details">
                <span className="demand-detail-chip">📦 {d.quantity_kg} kg</span>
                {d.max_price_per_kg && <span className="demand-detail-chip">💰 ≤₹{d.max_price_per_kg}/kg</span>}
                <span className="demand-detail-chip">📍 {d.delivery_address}</span>
                <span className="demand-detail-chip">⏰ {d.needed_by}</span>
                <span className="demand-detail-chip">{d.delivery_mode === 'delivery' ? '🚚 Delivery' : '📦 Pickup'}</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                Posted {formatDate(d.created_at)}
              </div>
            </div>
          ))}
        </>
      )}

      {deliveriesByBuyer.length > 0 && (
        <>
          <h3 style={{ marginTop: 20 }}>🚚 My Deliveries</h3>
          <p className="muted" style={{ margin: '0 0 8px', fontSize: '0.88rem' }}>
            {deliveriesByBuyer.length} delivery{deliveriesByBuyer.length !== 1 ? ' items' : ''}
          </p>
          {deliveriesByBuyer.map((dlv) => (
            <div key={dlv.id} className="delivery-card card">
              <div className="delivery-card-header">
                <h4>{dlv.product_name} — {dlv.quantity_kg} kg</h4>
                <span className={`status-pill status-${dlv.status}`}>{dlv.status.replace(/_/g, ' ')}</span>
              </div>
              <div className="delivery-info-grid">
                <div className="delivery-info-item">
                  <span className="info-label">Seller</span>
                  <span className="info-value">{dlv.seller_name}</span>
                </div>
                <div className="delivery-info-item">
                  <span className="info-label">Fee</span>
                  <span className="info-value">₹{dlv.delivery_fee.toFixed(0)}</span>
                </div>
                {dlv.delivery_address && (
                  <div className="delivery-info-item">
                    <span className="info-label">Address</span>
                    <span className="info-value">{dlv.delivery_address}</span>
                  </div>
                )}
                {dlv.eta && (
                  <div className="delivery-info-item">
                    <span className="info-label">ETA</span>
                    <span className="info-value">{dlv.eta}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
