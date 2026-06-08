import { useMemo, useState } from 'react';
import type { Listing } from '../types';

function formatGrade(grade: string): string {
  if (!grade) return 'Standard';
  return grade.charAt(0).toUpperCase() + grade.slice(1);
}

export default function OrderModal({
  listing,
  defaultBuyerName,
  defaultBuyerPhone,
  onClose,
  onSubmit,
}: {
  listing: Listing;
  defaultBuyerName?: string;
  defaultBuyerPhone?: string;
  onClose: () => void;
  onSubmit: (payload: {
    buyer_name: string;
    buyer_type: 'kirana' | 'restaurant' | 'canteen' | 'retailer';
    quantity_kg: number;
    pickup_time: string;
    phone?: string;
  }) => Promise<void>;
}) {
  const [buyerName, setBuyerName] = useState(defaultBuyerName || 'FreshBite Restaurant');
  const [buyerType, setBuyerType] = useState<'kirana' | 'restaurant' | 'canteen' | 'retailer'>('restaurant');
  const [quantity, setQuantity] = useState(20);
  const [pickupTime, setPickupTime] = useState('Today, 5:00 PM');
  const [phone, setPhone] = useState(defaultBuyerPhone || '');
  const [submitting, setSubmitting] = useState(false);

  const total = useMemo(() => (quantity * listing.price_per_kg).toFixed(2), [quantity, listing.price_per_kg]);

  return (
    <div className="modal-backdrop">
      <div className="modal card">
        <div className="modal-header">
          <h3>Order {listing.product_name}</h3>
          <button className="ghost-button" onClick={onClose}>Close</button>
        </div>

        <div className="form-grid">
          <div>
            <label className="label">Buyer name</label>
            <input value={buyerName} onChange={(e) => setBuyerName(e.target.value)} />
          </div>
          <div>
            <label className="label">Buyer type</label>
            <select value={buyerType} onChange={(e) => setBuyerType(e.target.value as typeof buyerType)}>
              <option value="restaurant">Restaurant</option>
              <option value="kirana">Kirana</option>
              <option value="canteen">Canteen</option>
              <option value="retailer">Retailer</option>
            </select>
          </div>
          <div>
            <label className="label">Quantity (kg)</label>
            <input type="number" max={listing.available_kg} value={quantity} onChange={(e) => setQuantity(Number(e.target.value || 0))} />
          </div>
          <div>
            <label className="label">Pickup time</label>
            <input value={pickupTime} onChange={(e) => setPickupTime(e.target.value)} />
          </div>
          <div>
            <label className="label">Phone</label>
            <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Optional" />
          </div>
        </div>

        <div className="summary-box">
          <div>Unit price: Rs {listing.price_per_kg}/kg</div>
          <div>Total: Rs {total}</div>
        </div>

        {(listing.quality_summary || listing.quality_score != null) && (
          <div className="summary-box quality-box">
            <div>
              Quality grade: {formatGrade(listing.quality_grade)}
              {listing.quality_score != null ? ` (${listing.quality_score}/100)` : ''}
            </div>
            {listing.quality_summary && <div>{listing.quality_summary}</div>}
            {listing.quality_assessment_source === 'ai_visual' && <div>Verified from the seller's produce photo.</div>}
          </div>
        )}

        <div className="action-row">
          <button className="ghost-button" onClick={onClose}>Cancel</button>
          <button
            className="primary-button"
            disabled={submitting || quantity <= 0 || quantity > listing.available_kg}
            onClick={async () => {
              setSubmitting(true);
              try {
                await onSubmit({
                  buyer_name: buyerName,
                  buyer_type: buyerType,
                  quantity_kg: quantity,
                  pickup_time: pickupTime,
                  phone,
                });
              } finally {
                setSubmitting(false);
              }
            }}
          >
            {submitting ? 'Placing...' : 'Confirm order'}
          </button>
        </div>
      </div>
    </div>
  );
}
