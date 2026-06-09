import { useState } from 'react';
import type { Delivery, FulfillmentDeliveryStatus } from '../types';

type DeliveryBoardProps = {
  deliveries: Delivery[];
  onAdvance: (deliveryId: string, status: FulfillmentDeliveryStatus) => Promise<void>;
  role: 'seller' | 'buyer' | 'ops';
};

const DELIVERY_STEPS: { key: FulfillmentDeliveryStatus; label: string }[] = [
  { key: 'order_accepted', label: 'Order Accepted' },
  { key: 'quality_check_pending', label: 'Quality Check' },
  { key: 'quality_approved', label: 'Quality Approved' },
  { key: 'packed', label: 'Packed' },
  { key: 'handover_pending', label: 'Ready for Pickup' },
  { key: 'picked_up', label: 'Picked Up' },
  { key: 'in_transit', label: 'In Transit' },
  { key: 'delivered', label: 'Delivered' },
  { key: 'buyer_confirmed', label: 'Buyer Confirmed' },
  { key: 'settled', label: 'Settled' },
];

const NEXT_STATUS_BY_ROLE: Record<'seller' | 'ops' | 'buyer', Partial<Record<FulfillmentDeliveryStatus, FulfillmentDeliveryStatus>>> = {
  seller: {
    order_accepted: 'packed',
    quality_approved: 'packed',
    packed: 'handover_pending',
  },
  ops: {
    order_accepted: 'quality_check_pending',
    quality_check_pending: 'quality_approved',
    quality_approved: 'picked_up',
    handover_pending: 'picked_up',
    packed: 'picked_up',
    picked_up: 'in_transit',
    in_transit: 'delivered',
    delivered: 'settled',
  },
  buyer: {
    delivered: 'buyer_confirmed',
  },
};

function labelForStatus(status: FulfillmentDeliveryStatus): string {
  const labels: Partial<Record<FulfillmentDeliveryStatus, string>> = {
    pending: 'Pending',
    accepted: 'Order Accepted',
    order_accepted: 'Order Accepted',
    quality_check_pending: 'Quality Pending',
    quality_approved: 'Quality Approved',
    quality_rejected: 'Quality Rejected',
    packed: 'Packed',
    handover_pending: 'Ready for Pickup',
    picked_up: 'Picked Up',
    out_for_delivery: 'In Transit',
    in_transit: 'In Transit',
    delivered: 'Delivered',
    buyer_confirmed: 'Buyer Confirmed',
    settled: 'Settled',
    cancelled: 'Cancelled',
  };
  return labels[status] || status.replace(/_/g, ' ');
}

function actorLabel(role: DeliveryBoardProps['role'] | null | undefined): string {
  if (role === 'ops') return 'Ops team';
  if (role === 'seller') return 'Seller';
  if (role === 'buyer') return 'Buyer';
  return 'System';
}

function deliveryErrorMessage(error: unknown): string {
  if (!(error instanceof Error) || !error.message) {
    return 'Could not update delivery status right now.';
  }
  if (error.message.toLowerCase().includes('invalid transition')) {
    return 'That delivery step is not available from the current stage.';
  }
  return error.message;
}

function stepIndex(status: FulfillmentDeliveryStatus): number {
  const canonical = status === 'accepted' ? 'order_accepted' : status === 'out_for_delivery' ? 'in_transit' : status;
  return DELIVERY_STEPS.findIndex((step) => step.key === canonical);
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
      setError(deliveryErrorMessage(err));
    } finally {
      setAdvancing(null);
    }
  };

  return (
    <div className="delivery-board slide-in">
      <h3>Managed Delivery</h3>

      {deliveries.length === 0 && (
        <div className="empty-state card">
          <div className="empty-icon">Truck</div>
          <strong>No deliveries yet</strong>
          <p>
            {role === 'seller'
              ? 'Accept orders or commit to a demand pool to start deliveries.'
              : role === 'ops'
                ? 'Ops-managed deliveries appear here after seller acceptance.'
              : 'Buyer deliveries will appear here after order acceptance.'}
          </p>
        </div>
      )}

      {deliveries.map((delivery) => {
        const currentIdx = stepIndex(delivery.status);
        const nextStatus = NEXT_STATUS_BY_ROLE[role][delivery.status];

        return (
          <div key={delivery.id} className="delivery-card card">
            <div className="delivery-card-header">
              <h4>{delivery.product_name} - {delivery.quantity_kg} kg</h4>
              <span className={`status-pill status-${delivery.status}`}>{labelForStatus(delivery.status)}</span>
            </div>

            <div className="delivery-info-grid">
              <div className="delivery-info-item">
                <span className="info-label">Seller</span>
                <span className="info-value">{delivery.seller_name}</span>
              </div>
              <div className="delivery-info-item">
                <span className="info-label">Buyer</span>
                <span className="info-value">{delivery.buyer_name}</span>
              </div>
              <div className="delivery-info-item">
                <span className="info-label">Mode</span>
              <span className="info-value">{delivery.delivery_mode === 'delivery' ? 'Managed Delivery' : 'Pickup'}</span>
              </div>
              <div className="delivery-info-item">
                <span className="info-label">Managed by</span>
                <span className="info-value">{actorLabel(delivery.current_actor_role || null)}</span>
              </div>
            </div>

            <div className="delivery-stepper">
              {DELIVERY_STEPS.map((step, idx) => (
                <div
                  key={step.key}
                  className={`delivery-step ${idx <= currentIdx ? 'delivery-step-done' : ''} ${idx === currentIdx ? 'delivery-step-active' : ''}`}
                >
                  <div className="delivery-step-dot">{idx + 1}</div>
                  <span className="delivery-step-label">{step.label}</span>
                </div>
              ))}
            </div>

            {nextStatus && (
              <div className="delivery-advance-row">
                <button
                  className="primary-button small"
                  disabled={advancing === delivery.id}
                  onClick={() => void handleAdvance(delivery.id, nextStatus)}
                >
                  {advancing === delivery.id ? 'Updating...' : `Advance to ${labelForStatus(nextStatus)}`}
                </button>
              </div>
            )}

            {error && <span className="error-text">{error}</span>}
          </div>
        );
      })}
    </div>
  );
}
