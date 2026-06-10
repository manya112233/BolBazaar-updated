import { useEffect, useMemo, useState } from 'react';
import { estimateDelivery } from '../api';
import { t, type Language } from '../i18n';
import type { DeliveryEstimate, Listing } from '../types';

function formatGrade(grade: string): string {
  if (!grade) return 'Standard';
  return grade.charAt(0).toUpperCase() + grade.slice(1);
}

export default function OrderModal({
  listing,
  language,
  defaultBuyerName,
  defaultBuyerPhone,
  onClose,
  onSubmit,
}: {
  listing: Listing;
  language: Language;
  defaultBuyerName?: string;
  defaultBuyerPhone?: string;
  onClose: () => void;
  onSubmit: (payload: {
    buyer_name: string;
    buyer_type: 'kirana' | 'restaurant' | 'canteen' | 'retailer';
    quantity_kg: number;
    pickup_time: string;
    phone?: string;
    delivery_mode?: 'pickup' | 'delivery';
    delivery_address?: string;
  }) => Promise<void>;
}) {
  const [buyerName, setBuyerName] = useState(defaultBuyerName || 'FreshBite Restaurant');
  const [buyerType, setBuyerType] = useState<'kirana' | 'restaurant' | 'canteen' | 'retailer'>('restaurant');
  const [quantity, setQuantity] = useState(20);
  const [pickupTime, setPickupTime] = useState('Today, 5:00 PM');
  const [phone, setPhone] = useState(defaultBuyerPhone || '');
  const [deliveryMode, setDeliveryMode] = useState<'pickup' | 'delivery'>('pickup');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [deliveryEstimate, setDeliveryEstimate] = useState<DeliveryEstimate | null>(null);
  const [estimateLoading, setEstimateLoading] = useState(false);
  const [estimateFailed, setEstimateFailed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (deliveryMode !== 'delivery' || !deliveryAddress.trim() || quantity <= 0) {
      setDeliveryEstimate(null);
      setEstimateFailed(false);
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setEstimateLoading(true);
      setEstimateFailed(false);
      void estimateDelivery({
        listing_id: listing.id,
        quantity_kg: quantity,
        delivery_address: deliveryAddress.trim(),
      })
        .then((value) => setDeliveryEstimate(value))
        .catch(() => {
          setDeliveryEstimate(null);
          setEstimateFailed(true);
        })
        .finally(() => setEstimateLoading(false));
    }, 500);

    return () => window.clearTimeout(timeoutId);
  }, [deliveryAddress, deliveryMode, listing.id, quantity]);

  const subtotal = useMemo(() => quantity * listing.price_per_kg, [quantity, listing.price_per_kg]);
  const deliveryFee = deliveryMode === 'delivery' ? deliveryEstimate?.total_delivery_fee || 0 : 0;
  const total = useMemo(() => (subtotal + deliveryFee).toFixed(2), [deliveryFee, subtotal]);

  return (
    <div className="modal-backdrop">
      <div className="modal card">
        <div className="modal-header">
          <h3>{t(language, 'orderModal.title', { product: listing.product_name })}</h3>
          <button className="ghost-button" onClick={onClose}>{t(language, 'common.close')}</button>
        </div>

        <div className="form-grid">
          <div>
            <label className="label">{t(language, 'orderModal.buyerName')}</label>
            <input value={buyerName} onChange={(event) => setBuyerName(event.target.value)} />
          </div>
          <div>
            <label className="label">{t(language, 'orderModal.buyerType')}</label>
            <select value={buyerType} onChange={(event) => setBuyerType(event.target.value as typeof buyerType)}>
              <option value="restaurant">Restaurant</option>
              <option value="kirana">Kirana</option>
              <option value="canteen">Canteen</option>
              <option value="retailer">Retailer</option>
            </select>
          </div>
          <div>
            <label className="label">{t(language, 'orderModal.quantity')}</label>
            <input type="number" max={listing.available_kg} value={quantity} onChange={(event) => setQuantity(Number(event.target.value || 0))} />
          </div>
          <div>
            <label className="label">{t(language, 'orderModal.pickupTime')}</label>
            <input value={pickupTime} onChange={(event) => setPickupTime(event.target.value)} />
          </div>
          <div>
            <label className="label">{t(language, 'orderModal.phone')}</label>
            <input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="Optional" />
          </div>
          <div>
            <label className="label">{t(language, 'orderModal.deliveryMode')}</label>
            <select value={deliveryMode} onChange={(event) => setDeliveryMode(event.target.value as typeof deliveryMode)}>
              <option value="pickup">{t(language, 'orderModal.pickup')}</option>
              <option value="delivery">{t(language, 'orderModal.delivery')}</option>
            </select>
          </div>
          {deliveryMode === 'delivery' ? (
            <div style={{ gridColumn: 'span 2' }}>
              <label className="label">{t(language, 'orderModal.deliveryAddress')}</label>
              <input value={deliveryAddress} onChange={(event) => setDeliveryAddress(event.target.value)} placeholder="e.g. Laxmi Nagar, Delhi" />
            </div>
          ) : null}
        </div>

        <div className="summary-box">
          <div>{t(language, 'orderModal.unitPrice')}: Rs {listing.price_per_kg}/kg</div>
          <div>{t(language, 'orderModal.subtotal')}: Rs {subtotal.toFixed(2)}</div>
          {deliveryMode === 'delivery' ? <div>{t(language, 'orderModal.deliveryFee')}: Rs {deliveryFee.toFixed(2)}</div> : null}
          <div>{t(language, 'orderModal.totalEstimate')}: Rs {total}</div>
          {estimateLoading ? <div>{t(language, 'orderModal.estimating')}</div> : null}
          {deliveryEstimate?.distance_km != null ? <div>{t(language, 'common.estimated')}: {deliveryEstimate.distance_km} km</div> : null}
          {deliveryMode === 'delivery' && !estimateLoading && (estimateFailed || (!deliveryEstimate && deliveryAddress.trim())) ? (
            <div>{t(language, 'orderModal.deliveryPending')}</div>
          ) : null}
        </div>

        {(listing.quality_summary || listing.quality_score != null) ? (
          <div className="summary-box quality-box">
            <div>
              {t(language, 'orderModal.qualityGrade')}: {formatGrade(listing.quality_grade)}
              {listing.quality_score != null ? ` (${listing.quality_score}/100)` : ''}
            </div>
            {listing.quality_summary ? <div>{listing.quality_summary}</div> : null}
            {listing.quality_assessment_source === 'ai_visual' ? <div>{t(language, 'orderModal.verifiedFromPhoto')}</div> : null}
          </div>
        ) : null}

        <div className="action-row">
          <button className="ghost-button" onClick={onClose}>{t(language, 'common.cancel')}</button>
          <button
            className="primary-button"
            disabled={submitting || quantity <= 0 || quantity > listing.available_kg || (deliveryMode === 'delivery' && !deliveryAddress.trim())}
            onClick={async () => {
              setSubmitting(true);
              try {
                await onSubmit({
                  buyer_name: buyerName,
                  buyer_type: buyerType,
                  quantity_kg: quantity,
                  pickup_time: pickupTime,
                  phone,
                  delivery_mode: deliveryMode,
                  delivery_address: deliveryMode === 'delivery' ? deliveryAddress.trim() : undefined,
                });
              } finally {
                setSubmitting(false);
              }
            }}
          >
            {submitting ? t(language, 'orderModal.placing') : t(language, 'orderModal.confirm')}
          </button>
        </div>
      </div>
    </div>
  );
}
