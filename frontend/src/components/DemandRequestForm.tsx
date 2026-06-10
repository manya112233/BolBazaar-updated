import { useState } from 'react';
import { t, type Language } from '../i18n';
import type { DemandRequestCreate } from '../types';

type DemandRequestFormProps = {
  buyerId: string;
  buyerName: string;
  language: Language;
  onSubmit: (payload: DemandRequestCreate) => Promise<void>;
};

export default function DemandRequestForm({ buyerId, buyerName, language, onSubmit }: DemandRequestFormProps) {
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
      window.setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit demand');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="demand-form-card card slide-in">
      <h3>{language === 'hi' ? 'मांग पोस्ट करें' : 'Post Your Demand'}</h3>
      <p className="form-subtitle">
        {language === 'hi'
          ? 'बताइए आपको क्या चाहिए। हम सही sellers ढूंढेंगे और मिलती-जुलती मांग को pool करेंगे।'
          : "Tell sellers what you need. We'll find strong matches and pool similar orders."}
      </p>

      <div className="demand-form-grid">
        <div className="full-span">
          <label className="label">{language === 'hi' ? 'क्या चाहिए?' : 'What do you need?'}</label>
          <input value={productQuery} onChange={(event) => setProductQuery(event.target.value)} placeholder="Tomato, potato, onion..." />
        </div>
        <div>
          <label className="label">{language === 'hi' ? 'मात्रा (किलो)' : 'Quantity (kg)'}</label>
          <input type="number" min={1} value={quantityKg} onChange={(event) => setQuantityKg(Number(event.target.value) || 0)} />
        </div>
        <div>
          <label className="label">{language === 'hi' ? 'अधिकतम रेट (वैकल्पिक)' : 'Max price per kg (optional)'}</label>
          <input type="number" min={1} value={maxPrice} onChange={(event) => setMaxPrice(event.target.value === '' ? '' : Number(event.target.value))} />
        </div>
        <div>
          <label className="label">{t(language, 'orderModal.deliveryMode')}</label>
          <select value={deliveryMode} onChange={(event) => setDeliveryMode(event.target.value as 'pickup' | 'delivery')}>
            <option value="delivery">{t(language, 'orderModal.delivery')}</option>
            <option value="pickup">{t(language, 'orderModal.pickup')}</option>
          </select>
        </div>
        <div>
          <label className="label">{language === 'hi' ? 'कब तक चाहिए' : 'Needed by'}</label>
          <input value={neededBy} onChange={(event) => setNeededBy(event.target.value)} />
        </div>
        <div className="full-span">
          <label className="label">{deliveryMode === 'delivery' ? t(language, 'orderModal.deliveryAddress') : (language === 'hi' ? 'लोकेशन' : 'Location')}</label>
          <input value={deliveryAddress} onChange={(event) => setDeliveryAddress(event.target.value)} placeholder="e.g. Laxmi Nagar, Delhi" />
        </div>
        <div>
          <label className="label">{t(language, 'orderModal.phone')}</label>
          <input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="+91 ..." />
        </div>
      </div>

      {error ? <p className="error-text" style={{ marginTop: 12 }}>{error}</p> : null}
      {success ? <div className="demand-form-success">{language === 'hi' ? 'मांग पोस्ट हो गई।' : 'Demand posted.'}</div> : null}

      <div className="demand-form-actions">
        <button className="primary-button" disabled={!canSubmit || submitting} onClick={handleSubmit}>
          {submitting ? t(language, 'orderModal.placing') : (language === 'hi' ? 'मांग पोस्ट करें' : 'Post Demand')}
        </button>
      </div>
    </div>
  );
}
