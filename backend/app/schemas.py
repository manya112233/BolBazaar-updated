from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


ProductCategory = Literal['vegetables', 'fruits', 'grains', 'spices', 'other']
OrderStatus = Literal['pending', 'accepted', 'rejected', 'completed']
ListingStatus = Literal['live', 'paused', 'sold_out']
SourceChannel = Literal['whatsapp', 'demo', 'api']
QualityAssessmentSource = Literal['text_signal', 'ai_visual']
ListingImageSource = Literal['seller_upload', 'produce_catalog', 'generic_catalog']
AuthRole = Literal['buyer', 'seller', 'ops']
NotificationRecipientRole = Literal['buyer', 'seller', 'ops', 'all']
NotificationCategory = Literal['order', 'delivery', 'demand', 'quality', 'pricing', 'ledger', 'system']
OtpDeliveryMethod = Literal['whatsapp', 'demo_preview']
OtpDeliveryStatus = Literal['sent', 'preview', 'failed']
SellerLanguage = Literal['hi', 'en']
SellerRegistrationStatus = Literal['pending', 'verification_pending', 'active']
SellerVerificationStatus = Literal['unverified', 'submitted', 'verified', 'manual_review']
SellerType = Literal['farmer', 'aggregator', 'fpo', 'trader']
LedgerEntryKind = Literal['sale', 'payment']
LedgerParseSource = Literal['rule_based', 'ai_structured']
LedgerCaptureMode = Literal['voice_note', 'text_message']
DeliveryMode = Literal['pickup', 'delivery']
DistanceSource = Literal['google_maps', 'haversine', 'unavailable']
ListingQualityStatus = Literal['pending', 'approved', 'rejected']
ListingQualityGrade = Literal['A', 'B', 'C']
FulfillmentDeliveryStatus = Literal[
    'pending',
    'accepted',
    'order_accepted',
    'quality_check_pending',
    'quality_approved',
    'quality_rejected',
    'packed',
    'handover_pending',
    'picked_up',
    'out_for_delivery',
    'in_transit',
    'delivered',
    'buyer_confirmed',
    'settled',
    'cancelled',
]
DeliveryPartnerStatus = Literal['available', 'assigned', 'offline']
DemandRequestStatus = Literal['open', 'pooled', 'committed', 'fulfilled', 'cancelled', 'expired']
DemandPoolStatus = Literal['forming', 'open', 'committed', 'fulfilling', 'fulfilled', 'expired']
SellerVerificationMethod = Literal[
    'farmer_registry',
    'pm_kisan',
    'enam',
    'fpo_certificate',
    'fssai',
    'govt_id',
    'other',
]
SellerSessionState = Literal[
    'awaiting_language',
    'awaiting_language_update',
    'awaiting_owner_name',
    'awaiting_profile_name_update',
    'awaiting_store_name_update',
    'awaiting_store_name',
    'awaiting_store_location',
    'awaiting_seller_type_update',
    'awaiting_seller_type',
    'awaiting_verification_method_update',
    'awaiting_verification_method',
    'awaiting_verification_number_update',
    'awaiting_verification_number',
    'awaiting_verification_proof_update',
    'awaiting_verification_proof',
    'awaiting_listing_message',
    'awaiting_listing_product',
    'awaiting_listing_quantity',
    'awaiting_listing_price',
    'awaiting_listing_confirmation',
]


class SellerMessageIn(BaseModel):
    seller_id: str
    seller_name: str
    message_text: str | None = None
    transcript_text: str | None = None
    image_url: HttpUrl | None = None
    audio_url: HttpUrl | None = None
    location_hint: str | None = None
    language_code: str = 'hi-IN'
    source_channel: SourceChannel = 'demo'


class BuyerDemandSearchIn(BaseModel):
    buyer_id: str = Field(min_length=2, max_length=120)
    search_query: str = Field(min_length=2, max_length=200)
    max_price_per_kg: float | None = Field(default=None, gt=0)
    quantity_kg: float | None = Field(default=None, gt=0)
    delivery_location: str | None = Field(default=None, max_length=200)
    needed_by: str | None = Field(default=None, max_length=120)
    buyer_type: Literal['kirana', 'restaurant', 'canteen', 'retailer'] | None = None


class OtpRequestIn(BaseModel):
    role: AuthRole
    phone_number: str = Field(min_length=10, max_length=20)


class OtpVerifyIn(BaseModel):
    request_id: str = Field(min_length=6, max_length=80)
    otp_code: str = Field(min_length=4, max_length=8)


class AuthSession(BaseModel):
    role: AuthRole
    phone_number: str
    seller_id: str | None = None
    seller_name: str | None = None
    store_name: str | None = None
    ops_id: str | None = None


class OtpRequestRecord(BaseModel):
    id: str = Field(default_factory=lambda: f'otp_{uuid4().hex[:10]}')
    role: AuthRole
    phone_number: str
    otp_code_hash: str
    delivery_method: OtpDeliveryMethod = 'demo_preview'
    delivery_status: OtpDeliveryStatus = 'preview'
    seller_id: str | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    verified_at: datetime | None = None
    failed_attempts: int = Field(default=0, ge=0)


class OtpRequestResponse(BaseModel):
    ok: bool = True
    request_id: str
    role: AuthRole
    phone_number: str
    expires_at: datetime
    delivery_method: OtpDeliveryMethod
    delivery_status: OtpDeliveryStatus
    note: str | None = None
    demo_otp: str | None = None


class OtpVerifyResponse(BaseModel):
    ok: bool = True
    session: AuthSession


class BuyerDemandEvent(BaseModel):
    id: str = Field(default_factory=lambda: f'dem_{uuid4().hex[:10]}')
    buyer_id: str
    search_query: str
    normalized_query: str
    detected_product_name: str | None = None
    detected_category: ProductCategory | None = None
    max_price_per_kg: float | None = None
    quantity_kg: float | None = None
    delivery_location: str | None = None
    needed_by: str | None = None
    buyer_type: str | None = None
    source_channel: SourceChannel = 'api'
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BuyerDemandSearchResponse(BaseModel):
    ok: bool = True
    event_id: str
    detected_product_name: str | None = None
    detected_category: ProductCategory | None = None
    unique_buyer_count: int = 0
    threshold: int = 0
    threshold_reached: bool = False
    notified_seller_count: int = 0
    reason: str | None = None


class DemandPoolOpportunity(BaseModel):
    id: str
    product_name: str
    category: ProductCategory | None = None
    total_quantity_kg: float = Field(ge=0)
    unique_buyer_count: int = Field(ge=0)
    average_max_price_per_kg: float | None = Field(default=None, ge=0)
    min_max_price_per_kg: float | None = Field(default=None, ge=0)
    max_max_price_per_kg: float | None = Field(default=None, ge=0)
    delivery_locations: list[str] = Field(default_factory=list)
    needed_by_labels: list[str] = Field(default_factory=list)
    buyer_types: list[str] = Field(default_factory=list)
    window_minutes: int = Field(ge=1)
    created_from_event_ids: list[str] = Field(default_factory=list)
    suggested_action: str
    urgency_label: str
    market_price_reference: MarketPriceReference | None = None


class DemandPoolResponse(BaseModel):
    items: list[DemandPoolOpportunity] = Field(default_factory=list)


class ProduceQualityAssessment(BaseModel):
    quality_grade: str = 'standard'
    quality_score: int | None = Field(default=None, ge=0, le=100)
    quality_summary: str | None = None
    quality_assessment_source: QualityAssessmentSource = 'text_signal'
    quality_signals: list[str] = Field(default_factory=list)
    detected_product_name: str | None = None
    detected_category: ProductCategory | None = None
    estimated_visible_count: int | None = Field(default=None, ge=0)


class DeliveryFeeBreakdown(BaseModel):
    distance_km: float | None = Field(default=None, ge=0)
    distance_source: DistanceSource = 'unavailable'
    base_fee: float = 0
    distance_fee: float = 0
    weight_fee: float = 0
    surge_fee: float = 0
    total_delivery_fee: float = 0
    currency: str = 'INR'
    fee_label: str = 'Estimated delivery fee'
    pricing_notes: list[str] = Field(default_factory=list)


class DeliveryEstimateIn(BaseModel):
    listing_id: str
    quantity_kg: float = Field(gt=0)
    delivery_address: str = Field(min_length=2, max_length=300)


class DeliveryEstimateResponse(BaseModel):
    listing_id: str
    seller_id: str
    seller_pickup_location: str
    delivery_address: str
    quantity_kg: float
    distance_km: float | None = Field(default=None, ge=0)
    distance_source: DistanceSource = 'unavailable'
    base_fee: float = 0
    distance_fee: float = 0
    weight_fee: float = 0
    surge_fee: float = 0
    total_delivery_fee: float = 0
    currency: str = 'INR'
    fee_label: str = 'Estimated delivery fee'
    pricing_notes: list[str] = Field(default_factory=list)


class MarketPriceReference(BaseModel):
    product_name: str
    normalized_commodity: str
    state: str | None = None
    district: str | None = None
    market: str | None = None
    mandi_min_price_per_kg: float | None = Field(default=None, ge=0)
    mandi_max_price_per_kg: float | None = Field(default=None, ge=0)
    mandi_modal_price_per_kg: float | None = Field(default=None, ge=0)
    mandi_modal_price_raw: float | None = Field(default=None, ge=0)
    raw_unit: str = 'quintal'
    arrival_date: str | None = None
    data_source: str = 'demo_fallback'
    confidence: float = Field(default=0.4, ge=0, le=1)
    suggested_price_per_kg: float | None = Field(default=None, ge=0)
    suggested_min_price_per_kg: float | None = Field(default=None, ge=0)
    suggested_max_price_per_kg: float | None = Field(default=None, ge=0)
    explanation: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class PricingSuggestionIn(BaseModel):
    product_name: str = Field(min_length=2, max_length=120)
    quality_grade: str | None = None
    seller_price_per_kg: float | None = Field(default=None, gt=0)
    pickup_location: str | None = None


class NotificationRecord(BaseModel):
    id: str = Field(default_factory=lambda: f'ntf_{uuid4().hex[:10]}')
    recipient_role: NotificationRecipientRole = 'seller'
    recipient_id: str | None = None
    seller_id: str | None = None
    order_id: str | None = None
    category: NotificationCategory = 'system'
    title: str
    text: str
    body: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    action_label: str | None = None
    action_target: str | None = None
    action_url: str | None = None
    audio_base64: str | None = None
    channel: str = 'web'
    delivery_status: str = 'simulated'
    read_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationReadAllIn(BaseModel):
    role: NotificationRecipientRole
    recipient_id: str | None = None


class ListingCreate(BaseModel):
    seller_id: str
    seller_name: str
    product_name: str
    category: ProductCategory = 'vegetables'
    quantity_kg: float = Field(gt=0)
    price_per_kg: float = Field(gt=0)
    pickup_location: str
    quality_grade: str = 'standard'
    quality_score: int | None = Field(default=None, ge=0, le=100)
    quality_summary: str | None = None
    quality_assessment_source: QualityAssessmentSource = 'text_signal'
    quality_signals: list[str] = Field(default_factory=list)
    quality_status: ListingQualityStatus = 'pending'
    quality_confidence: float | None = Field(default=None, ge=0, le=1)
    quality_notes: str | None = None
    quality_proof_images: list[str] = Field(default_factory=list)
    verified_by_bolbazaar: bool = False
    quality_checked_at: datetime | None = None
    quality_checked_by: str | None = None
    image_url: HttpUrl | None = None
    image_source: ListingImageSource | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None
    place_id: str | None = None
    market_reference_price_per_kg: float | None = Field(default=None, ge=0)
    suggested_price_per_kg: float | None = Field(default=None, ge=0)
    price_intelligence_note: str | None = None
    price_intelligence_source: str | None = None
    price_intelligence_updated_at: datetime | None = None
    source_channel: SourceChannel = 'api'
    raw_message: str | None = None


class Listing(BaseModel):
    id: str = Field(default_factory=lambda: f'lst_{uuid4().hex[:10]}')
    seller_id: str
    seller_name: str
    product_name: str
    category: ProductCategory = 'vegetables'
    quantity_kg: float
    available_kg: float
    price_per_kg: float
    pickup_location: str
    quality_grade: str = 'standard'
    quality_score: int | None = Field(default=None, ge=0, le=100)
    quality_summary: str | None = None
    quality_assessment_source: QualityAssessmentSource = 'text_signal'
    quality_signals: list[str] = Field(default_factory=list)
    quality_status: ListingQualityStatus = 'pending'
    quality_confidence: float | None = Field(default=None, ge=0, le=1)
    quality_notes: str | None = None
    quality_proof_images: list[str] = Field(default_factory=list)
    verified_by_bolbazaar: bool = False
    quality_checked_at: datetime | None = None
    quality_checked_by: str | None = None
    image_url: HttpUrl | None = None
    image_source: ListingImageSource | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None
    place_id: str | None = None
    market_reference_price_per_kg: float | None = Field(default=None, ge=0)
    suggested_price_per_kg: float | None = Field(default=None, ge=0)
    price_intelligence_note: str | None = None
    price_intelligence_source: str | None = None
    price_intelligence_updated_at: datetime | None = None
    source_channel: SourceChannel = 'api'
    raw_message: str | None = None
    status: ListingStatus = 'live'
    freshness_label: str = 'Fresh today'
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ListingResponse(BaseModel):
    items: list[Listing]


class OrderCreate(BaseModel):
    listing_id: str
    buyer_name: str
    buyer_type: Literal['kirana', 'restaurant', 'canteen', 'retailer'] = 'restaurant'
    quantity_kg: float = Field(gt=0)
    pickup_time: str
    phone: str | None = None
    buyer_phone: str | None = None
    delivery_mode: DeliveryMode = 'pickup'
    delivery_address: str | None = None


class Order(BaseModel):
    id: str = Field(default_factory=lambda: f'ord_{uuid4().hex[:10]}')
    listing_id: str
    seller_id: str
    seller_name: str
    product_name: str = 'items'
    buyer_name: str
    buyer_phone: str | None = None
    buyer_type: Literal['kirana', 'restaurant', 'canteen', 'retailer']
    quantity_kg: float
    pickup_time: str
    unit_price: float
    total_price: float
    produce_subtotal: float = 0
    status: OrderStatus = 'pending'
    delivery_mode: DeliveryMode = 'pickup'
    delivery_address: str | None = None
    delivery_distance_km: float | None = Field(default=None, ge=0)
    delivery_fee: float = 0
    buyer_total_payable: float = 0
    delivery_fee_breakdown: DeliveryFeeBreakdown | None = None
    fulfillment_status: FulfillmentDeliveryStatus = 'pending'
    quality_issue_reported: bool = False
    quality_issue_notes: str | None = None
    pool_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrderDecisionIn(BaseModel):
    decision: Literal['accept', 'reject']


class SellerInsight(BaseModel):
    seller_id: str
    headline: str
    message: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SellerProfile(BaseModel):
    seller_id: str
    seller_name: str
    store_name: str | None = None
    preferred_language: SellerLanguage = 'hi'
    seller_type: SellerType | None = None
    default_pickup_location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    place_id: str | None = None
    registration_status: SellerRegistrationStatus = 'pending'
    verification_status: SellerVerificationStatus = 'unverified'
    verification_method: SellerVerificationMethod | None = None
    verification_number: str | None = None
    verification_proof_url: str | None = None
    verification_notes: str | None = None
    source_channel: SourceChannel = 'whatsapp'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SellerSession(BaseModel):
    seller_id: str
    state: SellerSessionState
    draft_message: str | None = None
    draft_capture_mode: LedgerCaptureMode | None = None
    draft_quality_grade: str | None = None
    draft_quality_score: int | None = Field(default=None, ge=0, le=100)
    draft_quality_summary: str | None = None
    draft_quality_assessment_source: QualityAssessmentSource | None = None
    draft_quality_signals: list[str] = Field(default_factory=list)
    draft_detected_product_name: str | None = None
    draft_detected_category: ProductCategory | None = None
    draft_estimated_visible_count: int | None = Field(default=None, ge=0)
    draft_image_url: HttpUrl | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LedgerEntry(BaseModel):
    id: str = Field(default_factory=lambda: f'led_{uuid4().hex[:10]}')
    seller_id: str
    buyer_name: str
    entry_kind: LedgerEntryKind = 'sale'
    product_name: str | None = None
    quantity_kg: float | None = Field(default=None, ge=0)
    total_amount: float | None = Field(default=None, ge=0)
    amount_paid: float = Field(default=0, ge=0)
    amount_due: float = Field(default=0, ge=0)
    balance_delta: float = 0
    summary: str
    notes: str | None = None
    source_channel: SourceChannel = 'whatsapp'
    capture_mode: LedgerCaptureMode = 'text_message'
    parse_source: LedgerParseSource = 'rule_based'
    raw_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LedgerSummary(BaseModel):
    total_entries: int = 0
    total_outstanding_amount: float = 0
    total_collected_amount: float = 0
    buyers_with_balance: int = 0
    recent_entries: list[LedgerEntry] = Field(default_factory=list)


class SellerLedgerView(BaseModel):
    seller_id: str
    summary: LedgerSummary
    items: list[LedgerEntry] = Field(default_factory=list)


class LedgerPaymentCreate(BaseModel):
    buyer_name: str = Field(min_length=1, max_length=120)
    amount_paid: float = Field(gt=0)
    notes: str | None = Field(default=None, max_length=300)


class SellerDashboard(BaseModel):
    seller_id: str
    seller_name: str
    store_name: str | None = None
    preferred_language: SellerLanguage = 'hi'
    default_pickup_location: str | None = None
    live_listings_count: int = 0
    total_available_kg: float = 0
    sold_today_kg: float = 0
    sold_today_revenue: float = 0
    total_customers: int = 0
    repeat_customers: int = 0
    pending_orders: int = 0
    ledger_entries_count: int = 0
    ledger_outstanding_amount: float = 0
    ledger_collected_amount: float = 0
    ledger_buyers_with_balance: int = 0
    recent_customers: list[str] = Field(default_factory=list)
    recent_listings: list[Listing] = Field(default_factory=list)
    recent_ledger_entries: list[LedgerEntry] = Field(default_factory=list)
    recent_price_intelligence: list[MarketPriceReference] = Field(default_factory=list)


class DemoSeedResponse(BaseModel):
    ok: bool
    message: str


class SellerNotification(BaseModel):
    seller_id: str
    order_id: str
    text: str
    audio_base64: str | None = None
    channel: str = 'whatsapp'
    delivery_status: str = 'simulated'


class DemandRequestCreate(BaseModel):
    buyer_id: str = Field(min_length=2, max_length=120)
    buyer_name: str = Field(min_length=1, max_length=120)
    product_query: str = Field(min_length=2, max_length=200)
    quantity_kg: float = Field(gt=0)
    max_price_per_kg: float | None = Field(default=None, gt=0)
    delivery_mode: DeliveryMode = 'delivery'
    delivery_address: str = Field(min_length=2, max_length=300)
    needed_by: str = Field(min_length=2, max_length=120)
    phone: str | None = None


class DemandRequest(BaseModel):
    id: str = Field(default_factory=lambda: f'dmr_{uuid4().hex[:10]}')
    buyer_id: str
    buyer_name: str
    product_query: str
    product_name: str
    category: ProductCategory = 'vegetables'
    quantity_kg: float = Field(gt=0)
    max_price_per_kg: float | None = None
    delivery_mode: DeliveryMode = 'delivery'
    delivery_address: str
    latitude: float | None = None
    longitude: float | None = None
    place_id: str | None = None
    locality_key: str = 'unknown'
    needed_by: str
    phone: str | None = None
    status: DemandRequestStatus = 'open'
    pool_id: str | None = None
    order_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PoolMember(BaseModel):
    request_id: str
    buyer_id: str
    buyer_name: str
    quantity_kg: float
    delivery_address: str
    latitude: float | None = None
    longitude: float | None = None
    max_price_per_kg: float | None = None


class CommitDemandPool(BaseModel):   # persisted, commitable pool (distinct from DemandPoolOpportunity radar)
    id: str = Field(default_factory=lambda: f'cpool_{uuid4().hex[:10]}')
    product_name: str
    category: ProductCategory = 'vegetables'
    locality_key: str
    locality_label: str
    total_quantity_kg: float = 0
    buyer_count: int = 0
    suggested_max_price_per_kg: float | None = None
    centroid_lat: float | None = None
    centroid_lng: float | None = None
    members: list[PoolMember] = Field(default_factory=list)
    market_price_reference: MarketPriceReference | None = None
    status: DemandPoolStatus = 'open'
    committed_seller_id: str | None = None
    committed_seller_name: str | None = None
    committed_price_per_kg: float | None = None
    window_started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DeliveryPartner(BaseModel):
    id: str
    name: str
    phone: str
    vehicle_type: str
    vehicle_number: str
    status: DeliveryPartnerStatus = 'available'
    active: bool = True
    current_delivery_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PoolCommitIn(BaseModel):
    seller_id: str
    listing_id: str
    price_per_kg: float | None = Field(default=None, gt=0)


class Delivery(BaseModel):
    id: str = Field(default_factory=lambda: f'dlv_{uuid4().hex[:10]}')
    order_id: str
    pool_id: str | None = None
    seller_id: str
    seller_name: str
    buyer_id: str | None = None
    buyer_name: str
    product_name: str
    quantity_kg: float
    delivery_mode: DeliveryMode = 'delivery'
    delivery_address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_km: float | None = None
    delivery_fee: float = 0
    status: FulfillmentDeliveryStatus = 'accepted'
    current_actor_role: AuthRole | None = None
    last_actor_role: AuthRole | None = None
    last_actor_id: str | None = None
    handover_confirmed_at: datetime | None = None
    eta: str | None = None
    delivery_partner_id: str | None = None
    delivery_partner_name: str | None = None
    delivery_partner_phone: str | None = None
    delivery_partner_vehicle: str | None = None
    partner_assigned_at: datetime | None = None
    partner_assigned_by: str | None = None
    assignment_status: str | None = None
    buyer_phone: str | None = None
    pickup_scheduled_at: datetime | None = None
    pickup_slot_label: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DeliveryAdvanceIn(BaseModel):
    status: FulfillmentDeliveryStatus
    actor_role: AuthRole | None = None
    actor_id: str | None = None


class ListingQualityUpdateIn(BaseModel):
    status: ListingQualityStatus
    grade: ListingQualityGrade | None = None
    notes: str | None = None
    checked_by: str = Field(min_length=2, max_length=120)
    confidence: float | None = Field(default=None, ge=0, le=1)
    proof_images: list[str] = Field(default_factory=list)


class DeliveryAdvanceRequestIn(BaseModel):
    next_status: FulfillmentDeliveryStatus
    actor_role: AuthRole
    actor_id: str | None = None


class DeliveryPartnerAssignIn(BaseModel):
    partner_id: str
    assigned_by: str = Field(min_length=2, max_length=120)


class BuyerDeliveryConfirmIn(BaseModel):
    buyer_id: str = Field(min_length=2, max_length=120)
    quality_issue: bool = False
    notes: str | None = Field(default=None, max_length=500)


class OpsMetricSnapshot(BaseModel):
    total_listings: int = 0
    verified_listings: int = 0
    pending_quality_checks: int = 0
    rejected_listings: int = 0
    active_deliveries: int = 0
    completed_deliveries: int = 0
    demand_pools_matched: int = 0
    estimated_supply_matched_kg: float = 0
    orders_fulfilled_through_verified_supply: int = 0


class OpsDashboardResponse(BaseModel):
    pending_quality_checks: list[Listing] = Field(default_factory=list)
    verified_listings: list[Listing] = Field(default_factory=list)
    rejected_listings: list[Listing] = Field(default_factory=list)
    active_deliveries: list[Delivery] = Field(default_factory=list)
    metrics: OpsMetricSnapshot = Field(default_factory=OpsMetricSnapshot)

