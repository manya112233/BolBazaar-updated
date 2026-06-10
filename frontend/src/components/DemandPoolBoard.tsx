import { useState } from 'react';
import { t, type Language } from '../i18n';
import type { CommitDemandPool, Listing } from '../types';

type DemandPoolBoardProps = {
  pools: CommitDemandPool[];
  listings: Listing[];
  sellerId: string;
  language: Language;
  onCommit: (poolId: string, listingId: string, pricePerKg?: number) => Promise<void>;
};

export default function DemandPoolBoard({ pools, listings, sellerId, language, onCommit }: DemandPoolBoardProps) {
  const [commitPoolId, setCommitPoolId] = useState<string | null>(null);
  const [selectedListingId, setSelectedListingId] = useState('');
  const [commitPrice, setCommitPrice] = useState<number | ''>('');
  const [committing, setCommitting] = useState(false);

  const liveListings = listings.filter((item) => item.status === 'live' && item.seller_id === sellerId);

  return (
    <div className="pool-board slide-in">
      <h3>{t(language, 'demandPoolBoard.title')}</h3>
      {pools.length === 0 ? (
        <div className="empty-state card">
          <strong>{t(language, 'demandPoolBoard.none')}</strong>
        </div>
      ) : null}

      {pools.map((pool) => (
        <div key={pool.id} className="pool-card card">
          <div className="pool-card-header">
            <h4>{pool.product_name} - {pool.locality_label}</h4>
            <span className={`status-pill status-${pool.status}`}>{pool.status}</span>
          </div>
          <div className="pool-stats">
            <div className="pool-stat">
              <span className="pool-stat-value">{pool.total_quantity_kg} kg</span>
              <span className="pool-stat-label">{t(language, 'demandPoolBoard.totalDemand')}</span>
            </div>
            <div className="pool-stat">
              <span className="pool-stat-value">{pool.buyer_count}</span>
              <span className="pool-stat-label">{t(language, 'demandPoolBoard.buyers')}</span>
            </div>
            {pool.market_price_reference?.mandi_modal_price_per_kg ? (
              <div className="pool-stat">
                <span className="pool-stat-value">Rs {pool.market_price_reference.mandi_modal_price_per_kg}</span>
                <span className="pool-stat-label">{t(language, 'demandPoolBoard.mandiModal')}</span>
              </div>
            ) : null}
          </div>
          {pool.market_price_reference?.suggested_min_price_per_kg != null && pool.market_price_reference?.suggested_max_price_per_kg != null ? (
            <p className="bb-inline-note">
              {t(language, 'demandPoolBoard.suggestedPrice')} Rs {pool.market_price_reference.suggested_min_price_per_kg}-Rs {pool.market_price_reference.suggested_max_price_per_kg}/kg
            </p>
          ) : null}
          {pool.status === 'open' || pool.status === 'forming' ? (
            commitPoolId === pool.id ? (
              <div className="pool-commit-form">
                <select value={selectedListingId} onChange={(event) => setSelectedListingId(event.target.value)}>
                  <option value="">{t(language, 'demandPoolBoard.chooseListing')}</option>
                  {liveListings.map((listing) => (
                    <option key={listing.id} value={listing.id}>
                      {listing.product_name} - {listing.available_kg} kg @ Rs {listing.price_per_kg}/kg
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  min={1}
                  value={commitPrice}
                  onChange={(event) => setCommitPrice(event.target.value === '' ? '' : Number(event.target.value))}
                  placeholder={t(language, 'demandPoolBoard.price')}
                />
                <button
                  className="primary-button small"
                  disabled={!selectedListingId || committing}
                  onClick={async () => {
                    setCommitting(true);
                    try {
                      await onCommit(pool.id, selectedListingId, commitPrice === '' ? undefined : commitPrice);
                      setCommitPoolId(null);
                    } finally {
                      setCommitting(false);
                    }
                  }}
                >
                  {committing ? t(language, 'demandPoolBoard.committing') : t(language, 'demandPoolBoard.commitSupply')}
                </button>
              </div>
            ) : (
              <button
                className="primary-button small"
                disabled={liveListings.length === 0}
                onClick={() => {
                  setCommitPoolId(pool.id);
                  setSelectedListingId(liveListings[0]?.id || '');
                }}
              >
                {liveListings.length === 0 ? t(language, 'demandPoolBoard.noLiveListings') : t(language, 'demandPoolBoard.fulfillPool')}
              </button>
            )
          ) : null}
        </div>
      ))}
    </div>
  );
}
