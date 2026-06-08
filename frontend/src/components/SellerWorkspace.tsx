import { useState, useEffect } from 'react';
import type { AppLanguage } from '../App';
import type { AuthSession, DemandPoolOpportunity, CommitDemandPool, Delivery, Insight, Listing, Notification, Order, SellerDashboard, SellerLedgerView, SellerProfile, FulfillmentDeliveryStatus } from '../types';
import SellerOverview from './dashboard/SellerOverview';
import DemandPoolBoard from './DemandPoolBoard';
import DeliveryBoard from './DeliveryBoard';

type SellerTab = 'dashboard' | 'demand_pools' | 'deliveries';

export default function SellerWorkspace(props: {
  sectionId: string;
  language: AppLanguage;
  session: AuthSession;
  seller: SellerProfile | null;
  dashboard: SellerDashboard | null;
  ledger: SellerLedgerView | null;
  orders: Order[];
  notifications: Notification[];
  demandPools: DemandPoolOpportunity[];
  insight: Insight | null;
  loading: boolean;
  onRespondOrder: (orderId: string, decision: 'accept' | 'reject') => Promise<void>;
  onRecordLedgerPayment: (payload: { buyer_name: string; amount_paid: number; notes?: string }) => Promise<void>;
  // New props for pooling & delivery
  commitPools?: CommitDemandPool[];
  listings?: Listing[];
  deliveries?: Delivery[];
  onCommitPool?: (poolId: string, listingId: string, pricePerKg?: number) => Promise<void>;
  onAdvanceDelivery?: (deliveryId: string, status: FulfillmentDeliveryStatus) => Promise<void>;
}) {
  const [sellerTab, setSellerTab] = useState<SellerTab>('dashboard');

  useEffect(() => {
    setSellerTab('dashboard');
  }, [props.sectionId]);

  const tabs: { id: SellerTab; label: string; badge?: number }[] = [
    { id: 'dashboard', label: '🏪 Dashboard' },
    { id: 'demand_pools', label: '🤝 Demand Pools', badge: props.commitPools?.filter(p => p.status === 'open' || p.status === 'forming').length },
    { id: 'deliveries', label: '🚚 Deliveries', badge: props.deliveries?.filter(d => d.status !== 'delivered' && d.status !== 'cancelled').length },
  ];

  return (
    <div>
      <div className="workspace-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`workspace-tab ${sellerTab === tab.id ? 'workspace-tab-active' : ''}`}
            onClick={() => setSellerTab(tab.id)}
          >
            {tab.label}
            {tab.badge != null && tab.badge > 0 && <span className="tab-badge">{tab.badge}</span>}
          </button>
        ))}
      </div>

      {sellerTab === 'dashboard' && <SellerOverview {...props} />}

      {sellerTab === 'demand_pools' && props.onCommitPool && (
        <DemandPoolBoard
          pools={props.commitPools || []}
          listings={props.listings || []}
          sellerId={props.session.phone_number}
          onCommit={props.onCommitPool}
        />
      )}

      {sellerTab === 'deliveries' && props.onAdvanceDelivery && (
        <DeliveryBoard
          deliveries={props.deliveries || []}
          onAdvance={props.onAdvanceDelivery}
          role="seller"
        />
      )}
    </div>
  );
}
