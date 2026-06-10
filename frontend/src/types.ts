export type ProductCategory = 'vegetables' | 'fruits' | 'grains' | 'spices' | 'other';
export type ListingQualityStatus = 'pending' | 'approved' | 'rejected';
export type ListingQualityGrade = 'A' | 'B' | 'C';

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
  quality_status: ListingQualityStatus;
  quality_confidence?: number | null;
  quality_notes?: string | null;
  quality_proof_images: string[];
  verified_by_bolbazaar: boolean;
  quality_checked_at?: string | null;
  quality_checked_by?: string | null;
  image_url?: string | null;
  description?: string | null;
  tags: string[];
  latitude?: number | null;
  longitude?: number | null;
  place_id?: string | null;
  market_reference_price_per_kg?: number | null;
  suggested_price_per_kg?: number | null;
  price_intelligence_note?: string | null;
  price_intelligence_source?: string | null;
  price_intelligence_updated_at?: string | null;
  source_channel: 'whatsapp' | 'demo' | 'api';
  raw_message?: string | null;
  status: 'live' | 'paused' | 'sold_out';
  freshness_label: string;
  created_at: string;
};

export type AuthRole = 'buyer' | 'seller' | 'ops';

export type AuthSession = {
  role: AuthRole;
  phone_number: string;
  seller_id?: string | null;
  seller_name?: string | null;
  store_name?: string | null;
  ops_id?: string | null;
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
  buyer_phone?: string | null;
  buyer_type: 'kirana' | 'restaurant' | 'canteen' | 'retailer';
  quantity_kg: number;
  pickup_time: string;
  unit_price: number;
  total_price: number;
  produce_subtotal: number;
  status: 'pending' | 'accepted' | 'rejected' | 'completed';
  delivery_mode?: DeliveryMode;
  delivery_address?: string | null;
  delivery_distance_km?: number | null;
  delivery_fee: number;
  buyer_total_payable: number;
  delivery_fee_breakdown?: DeliveryFeeBreakdown | null;
  fulfillment_status?: FulfillmentDeliveryStatus;
  created_at: string;
};

export type NotificationRecipientRole = 'buyer' | 'seller' | 'ops' | 'all';
export type NotificationCategory = 'order' | 'delivery' | 'demand' | 'quality' | 'pricing' | 'ledger' | 'system';

export type Notification = {
  id: string;
  recipient_role: NotificationRecipientRole;
  recipient_id?: string | null;
  seller_id?: string | null;
  order_id?: string | null;
  category: NotificationCategory;
  title: string;
  text: string;
  body?: string | null;
  entity_type?: string | null;
  entity_id?: string | null;
  action_label?: string | null;
  action_target?: string | null;
  action_url?: string | null;
  audio_base64?: string | null;
  channel: string;
  delivery_status: string;
  read_at?: string | null;
  created_at: string;
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
  market_price_reference?: MarketPriceReference | null;
};

export type DemandPoolResponse = {
  items: DemandPoolOpportunity[];
};

export type DeliveryMode = 'pickup' | 'delivery';
export type FulfillmentDeliveryStatus =
  | 'pending'
  | 'accepted'
  | 'order_accepted'
  | 'quality_check_pending'
  | 'quality_approved'
  | 'quality_rejected'
  | 'packed'
  | 'handover_pending'
  | 'picked_up'
  | 'out_for_delivery'
  | 'in_transit'
  | 'delivered'
  | 'buyer_confirmed'
  | 'settled'
  | 'cancelled';
export type DemandRequestStatus = 'open' | 'pooled' | 'committed' | 'fulfilled' | 'cancelled' | 'expired';
export type DemandPoolStatus = 'forming' | 'open' | 'committed' | 'fulfilling' | 'fulfilled' | 'expired';

export type DemandRequestCreate = {
  buyer_id: string;
  buyer_name: string;
  product_query: string;
  quantity_kg: number;
  max_price_per_kg?: number | null;
  delivery_mode: DeliveryMode;
  delivery_address: string;
  needed_by: string;
  phone?: string | null;
};

export type DemandRequest = {
  id: string;
  buyer_id: string;
  buyer_name: string;
  product_query: string;
  product_name: string;
  category: ProductCategory;
  quantity_kg: number;
  max_price_per_kg?: number | null;
  delivery_mode: DeliveryMode;
  delivery_address: string;
  latitude?: number | null;
  longitude?: number | null;
  place_id?: string | null;
  locality_key: string;
  needed_by: string;
  phone?: string | null;
  status: DemandRequestStatus;
  pool_id?: string | null;
  order_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type PoolMember = {
  request_id: string;
  buyer_id: string;
  buyer_name: string;
  quantity_kg: number;
  delivery_address: string;
  latitude?: number | null;
  longitude?: number | null;
  max_price_per_kg?: number | null;
};

export type CommitDemandPool = {
  id: string;
  product_name: string;
  category: ProductCategory;
  locality_key: string;
  locality_label: string;
  total_quantity_kg: number;
  buyer_count: number;
  suggested_max_price_per_kg?: number | null;
  centroid_lat?: number | null;
  centroid_lng?: number | null;
  members: PoolMember[];
  market_price_reference?: MarketPriceReference | null;
  status: DemandPoolStatus;
  committed_seller_id?: string | null;
  committed_seller_name?: string | null;
  committed_price_per_kg?: number | null;
  window_started_at: string;
  updated_at: string;
};

export type PoolCommitIn = {
  seller_id: string;
  listing_id: string;
  price_per_kg?: number | null;
};

export type Delivery = {
  id: string;
  order_id: string;
  pool_id?: string | null;
  seller_id: string;
  seller_name: string;
  buyer_id?: string | null;
  buyer_name: string;
  product_name: string;
  quantity_kg: number;
  delivery_mode: DeliveryMode;
  delivery_address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  distance_km?: number | null;
  delivery_fee: number;
  status: FulfillmentDeliveryStatus;
  current_actor_role?: AuthRole | null;
  last_actor_role?: AuthRole | null;
  last_actor_id?: string | null;
  handover_confirmed_at?: string | null;
  eta?: string | null;
  created_at: string;
  updated_at: string;
};

export type DeliveryFeeBreakdown = {
  distance_km?: number | null;
  distance_source: 'google_maps' | 'haversine' | 'unavailable';
  base_fee: number;
  distance_fee: number;
  weight_fee: number;
  surge_fee: number;
  total_delivery_fee: number;
  currency: 'INR';
  fee_label: string;
  pricing_notes: string[];
};

export type DeliveryEstimate = {
  listing_id: string;
  seller_id: string;
  seller_pickup_location: string;
  delivery_address: string;
  quantity_kg: number;
  distance_km?: number | null;
  distance_source: 'google_maps' | 'haversine' | 'unavailable';
  base_fee: number;
  distance_fee: number;
  weight_fee: number;
  surge_fee: number;
  total_delivery_fee: number;
  currency: 'INR';
  fee_label: string;
  pricing_notes: string[];
};

export type MarketPriceReference = {
  product_name: string;
  normalized_commodity: string;
  state?: string | null;
  district?: string | null;
  market?: string | null;
  mandi_min_price_per_kg?: number | null;
  mandi_max_price_per_kg?: number | null;
  mandi_modal_price_per_kg?: number | null;
  mandi_modal_price_raw?: number | null;
  raw_unit: string;
  arrival_date?: string | null;
  data_source: string;
  confidence: number;
  suggested_price_per_kg?: number | null;
  suggested_min_price_per_kg?: number | null;
  suggested_max_price_per_kg?: number | null;
  explanation: string;
  fetched_at: string;
};

export type OpsMetricSnapshot = {
  total_listings: number;
  verified_listings: number;
  pending_quality_checks: number;
  rejected_listings: number;
  active_deliveries: number;
  completed_deliveries: number;
  demand_pools_matched: number;
  estimated_supply_matched_kg: number;
  orders_fulfilled_through_verified_supply: number;
};

export type OpsDashboardResponse = {
  pending_quality_checks: Listing[];
  verified_listings: Listing[];
  rejected_listings: Listing[];
  active_deliveries: Delivery[];
  metrics: OpsMetricSnapshot;
};
