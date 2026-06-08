import { useState } from 'react';
import type { DemandRequestCreate } from '../types';

type DemandRequestFormProps = {
  buyerId: string;
  buyerName: string;
  onSubmit: (payload: DemandRequestCreate) => Promise<void>;
};

export default function DemandRequestForm({ buyerId, buyerName, onSubmit }: DemandRequestFormProps) {
  const [productQuery, setProductQuery] = useState('');
  const [quantityKg, setQuantityKg] = useState(10);
  const [maxPrice, setMaxPrice] = useState<number | ''>('');
  const [deliveryMode, setDeliveryMode] = useState<'pickup' | 'delivery'>('delivery');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [neededBy, setNeededBy] = useState('Today evening');
  const [phone, setPhone] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = productQuery.trim().length >= 2 && quantityKg > 0 && deliveryAddress.trim().length >= 2 && neededBy.trim().length >= 2;

  const handleSubmit = async () => {
    if (!canSubmit || submitting) return;
    setSubmitting(true);
    setError(null);
    setSuccess(false);
    try {
      await onSubmit({
        buyer_id: buyerId,
        buyer_name: buyerName,
        product_query: productQuery.trim(),
        quantity_kg: quantityKg,
        max_price_per_kg: maxPrice === '' ? null : maxPrice,
        delivery_mode: deliveryMode,
        delivery_address: deliveryAddress.trim(),
        needed_by: neededBy.trim(),
        phone: phone.trim() || null,
      });
      setSuccess(true);
      setProductQuery('');
      setQuantityKg(10);
      setMaxPrice('');
      setDeliveryAddress('');
      setNeededBy('Today evening');
      setPhone('');
      setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit demand');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="demand-form-card card slide-in">
      <h3>📋 Post Your Demand</h3>
      <p className="form-subtitle">Tell sellers what you need — we'll find the best matches and pool similar orders for better prices.</p>

      <div className="demand-form-grid">
        <div className="full-span">
          <label className="label">What do you need?</label>
          <input
            value={productQuery}
            onChange={(e) => setProductQuery(e.target.value)}
            placeholder="e.g. Fresh tomatoes, Basmati rice, Green chillies..."
          />
        </div>

        <div>
          <label className="label">Quantity (kg)</label>
          <input
            type="number"
            min={1}
            value={quantityKg}
            onChange={(e) => setQuantityKg(Number(e.target.value) || 0)}
          />
        </div>

        <div>
          <label className="label">Max price per kg (₹) — optional</label>
          <input
            type="number"
            min={1}
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value === '' ? '' : Number(e.target.value))}
            placeholder="Any price"
          />
        </div>

        <div>
          <label className="label">Delivery mode</label>
          <select value={deliveryMode} onChange={(e) => setDeliveryMode(e.target.value as 'pickup' | 'delivery')}>
            <option value="delivery">🚚 Delivery to my address</option>
            <option value="pickup">📦 I'll pick up</option>
          </select>
        </div>

        <div>
          <label className="label">Needed by</label>
          <input
            value={neededBy}
            onChange={(e) => setNeededBy(e.target.value)}
            placeholder="e.g. Today 5 PM, Tomorrow morning"
          />
        </div>

        <div className="full-span">
          <label className="label">{deliveryMode === 'delivery' ? 'Delivery address' : 'Your location (for matching)'}</label>
          <input
            value={deliveryAddress}
            onChange={(e) => setDeliveryAddress(e.target.value)}
            placeholder="e.g. Laxmi Nagar, Delhi"
          />
        </div>

        <div>
          <label className="label">Phone (optional)</label>
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+91 ..."
          />
        </div>
      </div>

      {error && <p className="error-text" style={{ marginTop: 12 }}>{error}</p>}

      {success && (
        <div className="demand-form-success">
          ✅ Demand posted! We're matching you with nearby sellers.
        </div>
      )}

      <div className="demand-form-actions">
        <button
          className="primary-button"
          disabled={!canSubmit || submitting}
          onClick={handleSubmit}
        >
          {submitting ? 'Posting...' : '📣 Post Demand'}
        </button>
      </div>
    </div>
  );
}
