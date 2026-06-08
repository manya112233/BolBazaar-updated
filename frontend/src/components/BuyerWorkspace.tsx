import type { AppLanguage } from '../App';
import type { AuthSession, Insight, Listing, Notification, Order, SellerDashboard, SellerProfile } from '../types';
import BuyerOverview from './dashboard/BuyerOverview';

export default function BuyerWorkspace(props: {
  sectionId: string;
  language: AppLanguage;
  session: AuthSession;
  listings: Listing[];
  sellers: SellerProfile[];
  orders: Order[];
  notifications: Notification[];
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
}) {
  return <BuyerOverview {...props} />;
}
