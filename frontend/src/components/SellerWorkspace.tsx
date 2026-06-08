import type { AppLanguage } from '../App';
import type { AuthSession, DemandPoolOpportunity, Insight, Notification, Order, SellerDashboard, SellerLedgerView, SellerProfile } from '../types';
import SellerOverview from './dashboard/SellerOverview';

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
}) {
  return <SellerOverview {...props} />;
}
