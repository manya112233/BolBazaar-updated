import { t, type Language } from '../i18n';
import type { Delivery, DemandRequest } from '../types';

type MyDemandsPanelProps = {
  language: Language;
  demands: DemandRequest[];
  deliveries: Delivery[];
  onConfirmDelivery?: (deliveryId: string, qualityIssue?: boolean, notes?: string) => Promise<void>;
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
  } catch {
    return iso;
  }
}

export default function MyDemandsPanel({ language, demands, deliveries, onConfirmDelivery }: MyDemandsPanelProps) {
  return (
    <div className="demands-panel slide-in">
      <h3>{language === 'hi' ? 'मेरी मांग और डिलिवरी' : 'My Demands & Deliveries'}</h3>

      {demands.length === 0 && deliveries.length === 0 ? (
        <div className="empty-state card">
          <strong>{language === 'hi' ? 'अभी कोई मांग नहीं' : 'No demands yet'}</strong>
          <p>{language === 'hi' ? 'मांग पोस्ट करें, sellers आप तक पहुंचेंगे।' : 'Post a demand request and sellers will find you.'}</p>
        </div>
      ) : null}

      {demands.map((demand) => (
        <div key={demand.id} className="demand-card card">
          <div className="demand-card-header">
            <h4>{demand.product_name}</h4>
            <span className={`status-pill status-${demand.status}`}>{demand.status}</span>
          </div>
          <div className="demand-card-details">
            <span className="demand-detail-chip">{demand.quantity_kg} kg</span>
            {demand.max_price_per_kg ? <span className="demand-detail-chip">₹{demand.max_price_per_kg}/kg</span> : null}
            <span className="demand-detail-chip">{demand.delivery_address}</span>
            <span className="demand-detail-chip">{demand.needed_by}</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{formatDate(demand.created_at)}</div>
        </div>
      ))}

      {deliveries.map((delivery) => (
        <div key={delivery.id} className="delivery-card card">
          <div className="delivery-card-header">
            <h4>{delivery.product_name} - {delivery.quantity_kg} kg</h4>
            <span className={`status-pill status-${delivery.status}`}>{delivery.status.replace(/_/g, ' ')}</span>
          </div>
          <div className="delivery-info-grid">
            <div className="delivery-info-item">
              <span className="info-label">{language === 'hi' ? 'विक्रेता' : 'Seller'}</span>
              <span className="info-value">{delivery.seller_name}</span>
            </div>
            <div className="delivery-info-item">
              <span className="info-label">{t(language, 'orderModal.deliveryFee')}</span>
              <span className="info-value">₹{delivery.delivery_fee.toFixed(0)}</span>
            </div>
          </div>
          {onConfirmDelivery && delivery.status === 'delivered' ? (
            <div className="action-row" style={{ marginTop: 12 }}>
              <button className="primary-button small" onClick={() => void onConfirmDelivery(delivery.id, false)}>
                {language === 'hi' ? 'मिल गया' : 'Confirm received'}
              </button>
              <button className="ghost-button small" onClick={() => void onConfirmDelivery(delivery.id, true, 'Buyer raised a quality issue after delivery.')}>
                {language === 'hi' ? 'क्वालिटी समस्या' : 'Raise quality issue'}
              </button>
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
