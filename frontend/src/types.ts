export type ProductCategory = 'vegetables' | 'fruits' | 'grains' | 'spices' | 'other';

export type Listing = {
  id: string;
  seller_id: string;
  seller_name: string;
  product_name: string;
  category: ProductCategory;
  quantity_kg: number;
  available_kg: number;
  price_per_kg: number;
  pickup_location: string;
  quality_grade: string;
  quality_score?: number | null;
  quality_summary?: string | null;
  quality_assessment_source: 'text_signal' | 'ai_visual';
  quality_signals: string[];
  image_url?: string | null;
  description?: string | null;
  tags: string[];
  latitude?: number | null;
  longitude?: number | null;
  place_id?: string | null;
  source_channel: 'whatsapp' | 'demo' | 'api';
  raw_message?: string | null;
  status: 'live' | 'paused' | 'sold_out';
  freshness_label: string;
  created_at: string;
};

export type AuthRole = 'buyer' | 'seller';

export type AuthSession = {
  role: AuthRole;
  phone_number: string;
  seller_id?: string | null;
  seller_name?: string | null;
  store_name?: string | null;
};

export type OtpRequestResponse = {
  ok: boolean;
  request_id: string;
  role: AuthRole;
  phone_number: string;
  expires_at: string;
  delivery_method: 'whatsapp' | 'demo_preview';
  delivery_status: 'sent' | 'preview' | 'failed';
  note?: string | null;
  demo_otp?: string | null;
};

export type OtpVerifyResponse = {
  ok: boolean;
  session: AuthSession;
};

export type Order = {
  id: string;
  listing_id: string;
  seller_id: string;
  seller_name: string;
  product_name: string;
  buyer_name: string;
  buyer_type: 'kirana' | 'restaurant' | 'canteen' | 'retailer';
  quantity_kg: number;
  pickup_time: string;
  unit_price: number;
  total_price: number;
  status: 'pending' | 'accepted' | 'rejected' | 'completed';
  created_at: string;
};

export type Notification = {
  seller_id: string;
  order_id: string;
  text: string;
  audio_base64?: string | null;
  channel: string;
  delivery_status: string;
};

export type Insight = {
  seller_id: string;
  headline: string;
  message: string;
  generated_at: string;
};

export type SellerProfile = {
  seller_id: string;
  seller_name: string;
  store_name?: string | null;
  preferred_language: 'hi' | 'en';
  seller_type?: 'farmer' | 'aggregator' | 'fpo' | 'trader' | null;
  default_pickup_location?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  place_id?: string | null;
  registration_status: 'pending' | 'verification_pending' | 'active';
  verification_status?: 'unverified' | 'submitted' | 'verified' | 'manual_review';
  verification_method?: 'farmer_registry' | 'pm_kisan' | 'enam' | 'fpo_certificate' | 'fssai' | 'govt_id' | 'other' | null;
  verification_number?: string | null;
  verification_proof_url?: string | null;
  verification_notes?: string | null;
  source_channel: 'whatsapp' | 'demo' | 'api';
  created_at: string;
  updated_at: string;
};

export type LedgerEntry = {
  id: string;
  seller_id: string;
  buyer_name: string;
  entry_kind: 'sale' | 'payment';
  product_name?: string | null;
  quantity_kg?: number | null;
  total_amount?: number | null;
  amount_paid: number;
  amount_due: number;
  balance_delta: number;
  summary: string;
  notes?: string | null;
  source_channel: 'whatsapp' | 'demo' | 'api';
  capture_mode: 'voice_note' | 'text_message';
  parse_source: 'rule_based' | 'ai_structured';
  raw_message?: string | null;
  created_at: string;
};

export type LedgerSummary = {
  total_entries: number;
  total_outstanding_amount: number;
  total_collected_amount: number;
  buyers_with_balance: number;
  recent_entries: LedgerEntry[];
};

export type SellerLedgerView = {
  seller_id: string;
  summary: LedgerSummary;
  items: LedgerEntry[];
};

export type SellerDashboard = {
  seller_id: string;
  seller_name: string;
  store_name?: string | null;
  preferred_language: 'hi' | 'en';
  default_pickup_location?: string | null;
  live_listings_count: number;
  total_available_kg: number;
  sold_today_kg: number;
  sold_today_revenue: number;
  total_customers: number;
  repeat_customers: number;
  pending_orders: number;
  ledger_entries_count: number;
  ledger_outstanding_amount: number;
  ledger_collected_amount: number;
  ledger_buyers_with_balance: number;
  recent_customers: string[];
  recent_listings: Listing[];
  recent_ledger_entries: LedgerEntry[];
};

export type BuyerDemandSearchResponse = {
  ok: boolean;
  event_id: string;
  detected_product_name?: string | null;
  detected_category?: ProductCategory | null;
  unique_buyer_count: number;
  threshold: number;
  threshold_reached: boolean;
  notified_seller_count: number;
  reason?: string | null;
};

export type BuyerDemandSearchRequest = {
  buyer_id: string;
  search_query: string;
  max_price_per_kg?: number;
  quantity_kg?: number;
  delivery_location?: string;
  needed_by?: string;
  buyer_type?: 'kirana' | 'restaurant' | 'canteen' | 'retailer';
};

export type DemandPoolOpportunity = {
  id: string;
  product_name: string;
  category?: ProductCategory | null;
  total_quantity_kg: number;
  unique_buyer_count: number;
  average_max_price_per_kg?: number | null;
  min_max_price_per_kg?: number | null;
  max_max_price_per_kg?: number | null;
  delivery_locations: string[];
  needed_by_labels: string[];
  buyer_types: string[];
  window_minutes: number;
  created_from_event_ids: string[];
  suggested_action: string;
  urgency_label: string;
};

export type DemandPoolResponse = {
  items: DemandPoolOpportunity[];
};
