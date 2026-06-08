import { useState } from 'react';
import type { CommitDemandPool, Listing } from '../types';

type DemandPoolBoardProps = {
  pools: CommitDemandPool[];
  listings: Listing[];
  sellerId: string;
  onCommit: (poolId: string, listingId: string, pricePerKg?: number) => Promise<void>;
};

export default function DemandPoolBoard({ pools, listings, sellerId, onCommit }: DemandPoolBoardProps) {
  const [commitPoolId, setCommitPoolId] = useState<string | null>(null);
  const [selectedListingId, setSelectedListingId] = useState('');
  const [commitPrice, setCommitPrice] = useState<number | ''>('');
  const [committing, setCommitting] = useState(false);
  const [commitError, setCommitError] = useState<string | null>(null);

  const liveListings = listings.filter((l) => l.status === 'live' && l.seller_id === sellerId);

  const handleCommit = async (poolId: string) => {
    if (!selectedListingId || committing) return;
    setCommitting(true);
    setCommitError(null);
    try {
      await onCommit(poolId, selectedListingId, commitPrice === '' ? undefined : commitPrice);
      setCommitPoolId(null);
      setSelectedListingId('');
      setCommitPrice('');
    } catch (err) {
      setCommitError(err instanceof Error ? err.message : 'Commit failed');
    } finally {
      setCommitting(false);
    }
  };

  return (
    <div className="pool-board slide-in">
      <h3>🏪 Demand Pools — Supply Commitment</h3>
      <p className="pool-board-subtitle">
        Buyers near you have pooled their demand. Commit your produce to fulfill an entire pool and create coordinated deliveries.
      </p>

      {pools.length === 0 && (
        <div className="empty-state card">
          <div className="empty-icon">🔍</div>
          <strong>No active pools right now</strong>
          <p>When buyers in your area post demand, pools will appear here for you to fulfill.</p>
        </div>
      )}

      {pools.map((pool) => {
        const isCommitted = pool.status !== 'open' && pool.status !== 'forming';
        const isMyCommit = pool.committed_seller_id === sellerId;

        return (
          <div key={pool.id} className="pool-card card">
            <div className="pool-card-header">
              <h4>{pool.product_name} — {pool.locality_label}</h4>
              <span className={`status-pill status-${pool.status}`}>{pool.status}</span>
            </div>

            <div className="pool-stats">
              <div className="pool-stat">
                <span className="pool-stat-value">{pool.total_quantity_kg} kg</span>
                <span className="pool-stat-label">Total demand</span>
              </div>
              <div className="pool-stat">
                <span className="pool-stat-value">{pool.buyer_count}</span>
                <span className="pool-stat-label">Buyers</span>
              </div>
              {pool.suggested_max_price_per_kg && (
                <div className="pool-stat">
                  <span className="pool-stat-value">₹{pool.suggested_max_price_per_kg}</span>
                  <span className="pool-stat-label">Avg. max price/kg</span>
                </div>
              )}
            </div>

            <div className="pool-members">
              {pool.members.map((m) => (
                <div key={m.request_id} className="pool-member-row">
                  <strong>{m.buyer_name}</strong>
                  <span>{m.quantity_kg} kg</span>
                  <span className="muted">{m.delivery_address}</span>
                </div>
              ))}
            </div>

            {isCommitted && isMyCommit && (
              <div className="pool-committed-badge">
                ✅ You committed at ₹{pool.committed_price_per_kg}/kg — orders and deliveries created!
              </div>
            )}

            {isCommitted && !isMyCommit && (
              <div className="pool-committed-badge" style={{ background: 'rgba(148,163,184,0.08)', color: '#64748b' }}>
                Fulfilled by {pool.committed_seller_name || 'another seller'}
              </div>
            )}

            {!isCommitted && commitPoolId === pool.id && (
              <div className="pool-commit-form">
                <div className="field-group" style={{ flex: 1 }}>
                  <label>Select your listing</label>
                  <select value={selectedListingId} onChange={(e) => setSelectedListingId(e.target.value)}>
                    <option value="">Choose a listing...</option>
                    {liveListings.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.product_name} — {l.available_kg} kg @ ₹{l.price_per_kg}/kg
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field-group">
                  <label>Price per kg (₹)</label>
                  <input
                    type="number"
                    min={1}
                    value={commitPrice}
                    onChange={(e) => setCommitPrice(e.target.value === '' ? '' : Number(e.target.value))}
                    placeholder="Use listing price"
                  />
                </div>
                <button
                  className="primary-button small"
                  disabled={!selectedListingId || committing}
                  onClick={() => handleCommit(pool.id)}
                >
                  {committing ? 'Committing...' : '✅ Commit Supply'}
                </button>
                <button className="ghost-button small" onClick={() => { setCommitPoolId(null); setCommitError(null); }}>
                  Cancel
                </button>
                {commitError && <p className="error-text" style={{ width: '100%' }}>{commitError}</p>}
              </div>
            )}

            {!isCommitted && commitPoolId !== pool.id && (
              <button
                className="primary-button small"
                onClick={() => {
                  setCommitPoolId(pool.id);
                  setCommitError(null);
                  setSelectedListingId(liveListings[0]?.id || '');
                }}
                disabled={liveListings.length === 0}
              >
                {liveListings.length === 0 ? 'No live listings to commit' : '🤝 Fulfill this Pool'}
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
