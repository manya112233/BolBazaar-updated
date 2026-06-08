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
AuthRole = Literal['buyer', 'seller']
OtpDeliveryMethod = Literal['whatsapp', 'demo_preview']
OtpDeliveryStatus = Literal['sent', 'preview', 'failed']
SellerLanguage = Literal['hi', 'en']
SellerRegistrationStatus = Literal['pending', 'verification_pending', 'active']
SellerVerificationStatus = Literal['unverified', 'submitted', 'verified', 'manual_review']
SellerType = Literal['farmer', 'aggregator', 'fpo', 'trader']
LedgerEntryKind = Literal['sale', 'payment']
LedgerParseSource = Literal['rule_based', 'ai_structured']
LedgerCaptureMode = Literal['voice_note', 'text_message']
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


class ProduceQualityAssessment(BaseModel):
    quality_grade: str = 'standard'
    quality_score: int | None = Field(default=None, ge=0, le=100)
    quality_summary: str | None = None
    quality_assessment_source: QualityAssessmentSource = 'text_signal'
    quality_signals: list[str] = Field(default_factory=list)
    detected_product_name: str | None = None
    detected_category: ProductCategory | None = None
    estimated_visible_count: int | None = Field(default=None, ge=0)


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
    image_url: HttpUrl | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None
    place_id: str | None = None
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
    image_url: HttpUrl | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None
    place_id: str | None = None
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


class Order(BaseModel):
    id: str = Field(default_factory=lambda: f'ord_{uuid4().hex[:10]}')
    listing_id: str
    seller_id: str
    seller_name: str
    product_name: str = 'items'
    buyer_name: str
    buyer_type: Literal['kirana', 'restaurant', 'canteen', 'retailer']
    quantity_kg: float
    pickup_time: str
    unit_price: float
    total_price: float
    status: OrderStatus = 'pending'
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
