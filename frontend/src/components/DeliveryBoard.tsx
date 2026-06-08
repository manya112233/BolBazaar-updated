import { useState } from 'react';
import type { Delivery, FulfillmentDeliveryStatus } from '../types';

type DeliveryBoardProps = {
  deliveries: Delivery[];
  onAdvance: (deliveryId: string, status: FulfillmentDeliveryStatus) => Promise<void>;
  role: 'seller' | 'buyer';
};

const DELIVERY_STEPS: { key: FulfillmentDeliveryStatus; label: string; icon: string }[] = [
  { key: 'accepted', label: 'Accepted', icon: '✓' },
  { key: 'packed', label: 'Packed', icon: '📦' },
  { key: 'out_for_delivery', label: 'In Transit', icon: '🚚' },
  { key: 'delivered', label: 'Delivered', icon: '✅' },
];

const NEXT_STATUS: Partial<Record<FulfillmentDeliveryStatus, FulfillmentDeliveryStatus>> = {
  accepted: 'packed',
  packed: 'out_for_delivery',
  out_for_delivery: 'delivered',
};

function stepIndex(status: FulfillmentDeliveryStatus): number {
  if (status === 'cancelled') return -1;
  return DELIVERY_STEPS.findIndex((s) => s.key === status);
}

export default function DeliveryBoard({ deliveries, onAdvance, role }: DeliveryBoardProps) {
  const [advancing, setAdvancing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAdvance = async (deliveryId: string, nextStatus: FulfillmentDeliveryStatus) => {
    setAdvancing(deliveryId);
    setError(null);
    try {
      await onAdvance(deliveryId, nextStatus);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to advance');
    } finally {
      setAdvancing(null);
    }
  };

  return (
    <div className="delivery-board slide-in">
      <h3>🚚 Delivery Tracking</h3>

      {deliveries.length === 0 && (
        <div className="empty-state card">
          <div className="empty-icon">🚚</div>
          <strong>No deliveries yet</strong>
          <p>{role === 'seller' ? 'Commit to a demand pool or accept orders to start deliveries.' : 'Post a demand and your deliveries will appear here.'}</p>
        </div>
      )}

      {deliveries.map((dlv) => {
        const currentIdx = stepIndex(dlv.status);
        const next = NEXT_STATUS[dlv.status];
        const isCancelled = dlv.status === 'cancelled';

        return (
          <div key={dlv.id} className="delivery-card card">
            <div className="delivery-card-header">
              <h4>{dlv.product_name} — {dlv.quantity_kg} kg</h4>
              <span className={`status-pill status-${dlv.status}`}>{dlv.status.replace(/_/g, ' ')}</span>
            </div>

            <div className="delivery-info-grid">
              <div className="delivery-info-item">
                <span className="info-label">{role === 'seller' ? 'Buyer' : 'Seller'}</span>
                <span className="info-value">{role === 'seller' ? dlv.buyer_name : dlv.seller_name}</span>
              </div>
              {dlv.delivery_address && (
                <div className="delivery-info-item">
                  <span className="info-label">Address</span>
                  <span className="info-value">{dlv.delivery_address}</span>
                </div>
              )}
              <div className="delivery-info-item">
                <span className="info-label">Fee</span>
                <span className="info-value">₹{dlv.delivery_fee.toFixed(0)}</span>
              </div>
              {dlv.distance_km != null && (
                <div className="delivery-info-item">
                  <span className="info-label">Distance</span>
                  <span className="info-value">{dlv.distance_km.toFixed(1)} km</span>
                </div>
              )}
              <div className="delivery-info-item">
                <span className="info-label">Mode</span>
                <span className="info-value">{dlv.delivery_mode === 'delivery' ? '🚚 Delivery' : '📦 Pickup'}</span>
              </div>
            </div>

            {!isCancelled && (
              <div className="delivery-stepper">
                {DELIVERY_STEPS.map((step, idx) => {
                  const isDone = idx <= currentIdx;
                  const isActive = idx === currentIdx;
                  return (
                    <>
                      <div
                        key={step.key}
                        className={`delivery-step ${isDone ? 'delivery-step-done' : ''} ${isActive ? 'delivery-step-active' : ''}`}
                      >
                        <div className="delivery-step-dot">{step.icon}</div>
                        <span className="delivery-step-label">{step.label}</span>
                      </div>
                      {idx < DELIVERY_STEPS.length - 1 && (
                        <div className={`delivery-step-line ${idx < currentIdx ? 'delivery-step-line-done' : ''}`} />
                      )}
                    </>
                  );
                })}
              </div>
            )}

            {isCancelled && (
              <div style={{ padding: '10px 14px', borderRadius: 12, background: 'rgba(239,68,68,0.06)', color: '#b91c1c', fontWeight: 600 }}>
                ❌ This delivery was cancelled
              </div>
            )}

            {role === 'seller' && next && (
              <div className="delivery-advance-row">
                <button
                  className="primary-button small"
                  disabled={advancing === dlv.id}
                  onClick={() => handleAdvance(dlv.id, next)}
                >
                  {advancing === dlv.id ? 'Updating...' : `Advance → ${next.replace(/_/g, ' ')}`}
                </button>
                {dlv.status !== 'delivered' && (
                  <button
                    className="ghost-button small"
                    disabled={advancing === dlv.id}
                    onClick={() => handleAdvance(dlv.id, 'cancelled')}
                  >
                    Cancel delivery
                  </button>
                )}
                {error && advancing === null && <span className="error-text">{error}</span>}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
