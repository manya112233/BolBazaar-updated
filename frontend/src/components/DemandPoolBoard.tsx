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
  const [commitPrice, setCommitPrice] = useState<number | ''>('');
  const [committing, setCommitting] = useState(false);
  const [committedPrices, setCommittedPrices] = useState<Record<string, number>>({});

  const liveListings = listings.filter((item) => item.status === 'live' && item.seller_id === sellerId);

  return (
    <div className="pool-board slide-in">
      <h3>{t(language, 'demandPoolBoard.title')}</h3>
      {pools.length === 0 ? (
        <div className="empty-state card">
          <strong>{t(language, 'demandPoolBoard.none')}</strong>
        </div>
      ) : null}

      {pools.map((pool) => {
        const ref = pool.market_price_reference;
        const mandiPrice = ref?.mandi_modal_price_per_kg;
        const suggestedMin = ref?.suggested_min_price_per_kg;
        const suggestedMax = ref?.suggested_max_price_per_kg;
        const listedPrice = liveListings[0]?.price_per_kg;
        const committedPrice = committedPrices[pool.id];

        return (
          <div key={pool.id} className="pool-card card">
            <div className="pool-card-header">
              <h4>{pool.product_name} — {pool.locality_label}</h4>
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
              {committedPrice ? (
                <div className="pool-stat pool-stat--committed">
                  <span className="pool-stat-value">Rs {committedPrice}/kg</span>
                  <span className="pool-stat-label">Your committed price</span>
                </div>
              ) : null}
            </div>

            {/* Price reference cards */}
            {(mandiPrice || (suggestedMin != null && suggestedMax != null) || listedPrice) ? (
              <div className="pool-price-refs">
                {mandiPrice ? (
                  <div className="pool-price-ref">
                    <span className="pool-price-ref-label">Mandi modal price</span>
                    <span className="pool-price-ref-value">Rs {mandiPrice}/kg</span>
                    <span className="pool-price-ref-hint">Today's wholesale market rate</span>
                  </div>
                ) : null}
                {suggestedMin != null && suggestedMax != null ? (
                  <div className="pool-price-ref pool-price-ref--suggested">
                    <span className="pool-price-ref-label">Suggested range</span>
                    <span className="pool-price-ref-value">Rs {suggestedMin}–{suggestedMax}/kg</span>
                    <span className="pool-price-ref-hint">Recommended for this pool</span>
                  </div>
                ) : null}
                {listedPrice ? (
                  <div className="pool-price-ref">
                    <span className="pool-price-ref-label">Your listed price</span>
                    <span className="pool-price-ref-value">Rs {listedPrice}/kg</span>
                    <span className="pool-price-ref-hint">From your active listing</span>
                  </div>
                ) : null}
              </div>
            ) : null}

            {pool.status === 'open' || pool.status === 'forming' ? (
              commitPoolId === pool.id ? (
                <div className="pool-commit-form">
                  <label className="pool-commit-label">
                    Your supply price (Rs/kg)
                    <input
                      type="number"
                      min={1}
                      value={commitPrice}
                      onChange={(event) => setCommitPrice(event.target.value === '' ? '' : Number(event.target.value))}
                      placeholder="Enter your price per kg"
                    />
                  </label>
                  <div className="pool-commit-actions">
                    <button
                      className="primary-button small"
                      disabled={committing}
                      onClick={async () => {
                        const listing = liveListings[0];
                        if (!listing) return;
                        setCommitting(true);
                        try {
                          const finalPrice = commitPrice === '' ? undefined : commitPrice;
                          await onCommit(pool.id, listing.id, finalPrice);
                          if (finalPrice !== undefined) {
                            setCommittedPrices((prev) => ({ ...prev, [pool.id]: finalPrice as number }));
                          }
                          setCommitPoolId(null);
                          setCommitPrice('');
                        } finally {
                          setCommitting(false);
                        }
                      }}
                    >
                      {committing ? t(language, 'demandPoolBoard.committing') : t(language, 'demandPoolBoard.commitSupply')}
                    </button>
                    <button className="ghost-button small" onClick={() => { setCommitPoolId(null); setCommitPrice(''); }}>
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  className="primary-button small"
                  disabled={liveListings.length === 0}
                  onClick={() => {
                    setCommitPoolId(pool.id);
                    setCommitPrice('');
                  }}
                >
                  {liveListings.length === 0 ? t(language, 'demandPoolBoard.noLiveListings') : t(language, 'demandPoolBoard.fulfillPool')}
                </button>
              )
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
