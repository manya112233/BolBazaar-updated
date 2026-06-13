import { useState } from 'react';
import { t, type Language } from '../i18n';
import type { Delivery, FulfillmentDeliveryStatus } from '../types';

type DeliveryBoardProps = {
  deliveries: Delivery[];
  onAdvance: (deliveryId: string, status: FulfillmentDeliveryStatus) => Promise<void>;
  role: 'seller' | 'buyer' | 'ops';
  language: Language;
};

const NEXT_STATUS_BY_ROLE: Record<'seller' | 'ops' | 'buyer', Partial<Record<FulfillmentDeliveryStatus, FulfillmentDeliveryStatus>>> = {
  seller: { order_accepted: 'packed', quality_approved: 'packed', packed: 'handover_pending' },
  ops: { order_accepted: 'quality_check_pending', quality_check_pending: 'quality_approved', quality_approved: 'picked_up', handover_pending: 'picked_up', packed: 'picked_up', picked_up: 'in_transit', in_transit: 'delivered', delivered: 'settled' },
  buyer: { delivered: 'buyer_confirmed' },
};

const DELIVERY_FLOW: FulfillmentDeliveryStatus[] = [
  'order_accepted',
  'packed',
  'picked_up',
  'in_transit',
  'delivered',
  'buyer_confirmed',
  'settled',
];

const DELIVERY_FLOW_LABELS: Record<FulfillmentDeliveryStatus, string> = {
  pending: 'Pending',
  accepted: 'Accepted',
  order_accepted: 'Accepted',
  quality_check_pending: 'Quality check',
  quality_approved: 'Quality approved',
  quality_rejected: 'Quality rejected',
  packed: 'Packed',
  handover_pending: 'Handover',
  picked_up: 'Picked up',
  out_for_delivery: 'Out for delivery',
  in_transit: 'In transit',
  delivered: 'Delivered',
  buyer_confirmed: 'Buyer confirmed',
  settled: 'Settled',
  cancelled: 'Cancelled',
};

function normalizeDeliveryStage(status: FulfillmentDeliveryStatus): FulfillmentDeliveryStatus {
  if (status === 'accepted') return 'order_accepted';
  if (status === 'quality_check_pending' || status === 'quality_approved' || status === 'handover_pending') return 'packed';
  if (status === 'out_for_delivery') return 'in_transit';
  return status;
}

function statusIndex(status: FulfillmentDeliveryStatus): number {
  return DELIVERY_FLOW.indexOf(normalizeDeliveryStage(status));
}

export default function DeliveryBoard({ deliveries, onAdvance, role, language }: DeliveryBoardProps) {
  const [advancing, setAdvancing] = useState<string | null>(null);

  if (deliveries.length === 0) {
    return (
      <div className="empty-state card">
        <strong>{t(language, 'deliveryBoard.none')}</strong>
      </div>
    );
  }

  return (
    <div className="delivery-board slide-in">
      <h3>{t(language, 'deliveryBoard.title')}</h3>
      {deliveries.map((delivery) => {
        const nextStatus = NEXT_STATUS_BY_ROLE[role][delivery.status];
        const currentStepIndex = statusIndex(delivery.status);
        return (
          <div key={delivery.id} className="delivery-card card">
            <div className="delivery-card-header">
              <h4>{delivery.product_name} - {delivery.quantity_kg} kg</h4>
              <span className={`status-pill status-${delivery.status}`}>{delivery.status.replace(/_/g, ' ')}</span>
            </div>
            {delivery.status !== 'cancelled' ? (
              <div className="delivery-stepper" aria-label="Delivery progress">
                {DELIVERY_FLOW.map((step, index) => {
                  const isDone = currentStepIndex > index;
                  const isActive = currentStepIndex === index;
                  return (
                    <div
                      key={step}
                      className={`delivery-step${isDone ? ' delivery-step-done' : ''}${isActive ? ' delivery-step-active' : ''}`}
                    >
                      <div className="delivery-step-dot">
                        {index + 1}
                      </div>
                      <span className="delivery-step-label">
                        {DELIVERY_FLOW_LABELS[step]}
                      </span>
                      {index < DELIVERY_FLOW.length - 1 ? (
                        <div className={`delivery-step-line${currentStepIndex > index ? ' delivery-step-line-done' : ''}`} />
                      ) : null}
                    </div>
                  );
                })}
              </div>
            ) : null}
            <div className="delivery-info-grid">
              <div className="delivery-info-item">
                <span className="info-label">{t(language, 'deliveryBoard.buyer')}</span>
                <span className="info-value">{delivery.buyer_name}</span>
              </div>
              <div className="delivery-info-item">
                <span className="info-label">{t(language, 'deliveryBoard.deliveryFee')}</span>
                <span className="info-value">Rs {delivery.delivery_fee}</span>
              </div>
              {delivery.distance_km != null ? (
                <div className="delivery-info-item">
                  <span className="info-label">{t(language, 'deliveryBoard.distance')}</span>
                  <span className="info-value">{delivery.distance_km} km</span>
                </div>
              ) : null}
              {delivery.pickup_slot_label ? (
                <div className="delivery-info-item">
                  <span className="info-label">{language === 'hi' ? 'à¤ªà¤¿à¤•à¤…à¤ª à¤¸à¤®à¤¯' : 'Pickup'}</span>
                  <span className="info-value">{delivery.pickup_slot_label}</span>
                </div>
              ) : null}
              {delivery.delivery_partner_name ? (
                <div className="delivery-info-item">
                  <span className="info-label">{language === 'hi' ? 'à¤ªà¤¾à¤°à¥à¤Ÿà¤¨à¤°' : 'Partner'}</span>
                  <span className="info-value">{delivery.delivery_partner_name} {delivery.delivery_partner_id ? `(${delivery.delivery_partner_id})` : ''}</span>
                </div>
              ) : null}
              {delivery.delivery_partner_vehicle ? (
                <div className="delivery-info-item">
                  <span className="info-label">{language === 'hi' ? 'à¤µà¤¾à¤¹à¤¨' : 'Vehicle'}</span>
                  <span className="info-value">{delivery.delivery_partner_vehicle}</span>
                </div>
              ) : null}
              {delivery.delivery_partner_phone ? (
                <div className="delivery-info-item">
                  <span className="info-label">{language === 'hi' ? 'à¤«à¥‹à¤¨' : 'Phone'}</span>
                  <span className="info-value">{delivery.delivery_partner_phone}</span>
                </div>
              ) : null}
              {delivery.assignment_status ? (
                <div className="delivery-info-item">
                  <span className="info-label">{language === 'hi' ? 'à¤…à¤¸à¤¾à¤‡à¤¨à¤®à¥‡à¤‚à¤Ÿ' : 'Assignment'}</span>
                  <span className="info-value">{delivery.assignment_status}</span>
                </div>
              ) : null}
            </div>
            {nextStatus ? (
              <div className="delivery-advance-row">
                <button
                  className="primary-button small"
                  disabled={advancing === delivery.id}
                  onClick={async () => {
                    setAdvancing(delivery.id);
                    try {
                      await onAdvance(delivery.id, nextStatus);
                    } finally {
                      setAdvancing(null);
                    }
                  }}
                >
                  {advancing === delivery.id ? t(language, 'deliveryBoard.updating') : `${t(language, 'deliveryBoard.advanceTo')} ${nextStatus.replace(/_/g, ' ')}`}
                </button>
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
