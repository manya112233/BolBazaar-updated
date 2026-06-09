import { useEffect, useState } from 'react';
import type { AppLanguage } from '../App';
import type {
  AuthSession,
  BuyerDemandSearchRequest,
  Delivery,
  DemandPoolOpportunity,
  DemandRequest,
  DemandRequestCreate,
  Insight,
  Listing,
  Notification,
  Order,
  SellerDashboard,
  SellerProfile,
} from '../types';
import BuyerOverview from './dashboard/BuyerOverview';
import DemandRequestForm from './DemandRequestForm';
import MyDemandsPanel from './MyDemandsPanel';

type BuyerTab = 'browse' | 'post_demand' | 'my_demands';

export default function BuyerWorkspace(props: {
  sectionId: string;
  language: AppLanguage;
  session: AuthSession;
  listings: Listing[];
  sellers: SellerProfile[];
  orders: Order[];
  notifications: Notification[];
  demandPools: DemandPoolOpportunity[];
  dashboard: SellerDashboard | null;
  insight: Insight | null;
  selectedSellerId: string | null;
  query: string;
  maxPrice: number;
  loading: boolean;
  onSelectSeller: (sellerId: string) => void;
  onQueryChange: (value: string) => void;
  onMaxPriceChange: (value: number) => void;
  onOrder: (listing: Listing) => void;
  onCreateDemand: (payload: BuyerDemandSearchRequest) => Promise<void>;
  buyerDemands?: DemandRequest[];
  buyerDeliveries?: Delivery[];
  onPostDemandRequest?: (payload: DemandRequestCreate) => Promise<void>;
  onConfirmDelivery?: (deliveryId: string, qualityIssue?: boolean, notes?: string) => Promise<void>;
}) {
  const [buyerTab, setBuyerTab] = useState<BuyerTab>('browse');

  useEffect(() => {
    setBuyerTab('browse');
  }, [props.sectionId]);

  const tabs: { id: BuyerTab; label: string; badge?: number }[] = [
    { id: 'browse', label: 'Browse Marketplace' },
    { id: 'post_demand', label: 'Post Demand' },
    {
      id: 'my_demands',
      label: 'My Demand & Delivery',
      badge: (props.buyerDemands?.length || 0) + (props.buyerDeliveries?.length || 0),
    },
  ];

  return (
    <div>
      <div className="workspace-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`workspace-tab ${buyerTab === tab.id ? 'workspace-tab-active' : ''}`}
            onClick={() => setBuyerTab(tab.id)}
          >
            {tab.label}
            {tab.badge != null && tab.badge > 0 && <span className="tab-badge">{tab.badge}</span>}
          </button>
        ))}
      </div>

      {buyerTab === 'browse' && <BuyerOverview {...props} />}

      {buyerTab === 'post_demand' && props.onPostDemandRequest && (
        <DemandRequestForm
          buyerId={props.session.phone_number}
          buyerName={props.session.store_name || `Buyer ${props.session.phone_number.slice(-4)}`}
          onSubmit={props.onPostDemandRequest}
        />
      )}

      {buyerTab === 'my_demands' && (
        <MyDemandsPanel
          demands={props.buyerDemands || []}
          deliveries={props.buyerDeliveries || []}
          onConfirmDelivery={props.onConfirmDelivery}
        />
      )}
    </div>
  );
}
