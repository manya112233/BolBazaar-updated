import type { AppLanguage } from '../App';
import type { AuthSession, BuyerDemandSearchRequest, DemandPoolOpportunity, Insight, Listing, Notification, Order, SellerDashboard, SellerProfile } from '../types';
import BuyerOverview from './dashboard/BuyerOverview';

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
}) {
  return <BuyerOverview {...props} />;
}
