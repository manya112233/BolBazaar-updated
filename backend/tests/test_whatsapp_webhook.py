from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.dependencies import get_marketplace, get_store
from app.main import app
from app.schemas import LedgerEntry, Listing, Order, ProduceQualityAssessment, SellerProfile, SellerSession
from app.services.extraction import ExtractionService
from app.services.marketplace import MarketplaceService
from app.services.seller_flow import MENU_ACTION_ORDERS, MENU_ACTION_VERIFICATION, SellerFlowService
from app.services.store import JsonStore
from app.services.whatsapp_service import MAX_LIST_ROWS, WhatsAppService


class StubMarketplace:
    def __init__(self) -> None:
        self.calls = 0
        self.last_quality_assessment: ProduceQualityAssessment | None = None

    def create_listing_from_message(
        self,
        *,
        seller_id: str,
        seller_name: str,
        message_text: str,
        image_url: str | None,
        source_channel: str = 'api',
        default_pickup_location: str | None = None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        quality_assessment: ProduceQualityAssessment | None = None,
    ) -> Listing:
        self.calls += 1
        self.last_quality_assessment = quality_assessment
        public_image_url = image_url if image_url and image_url.startswith(('http://', 'https://')) else None
        return Listing(
            seller_id=seller_id,
            seller_name=seller_name,
            product_name='Tomato',
            category='vegetables',
            quantity_kg=50.0,
            available_kg=50.0,
            price_per_kg=28.0,
            pickup_location=default_pickup_location or 'Laxmi Nagar',
            quality_grade=(quality_assessment.quality_grade if quality_assessment else 'standard'),
            quality_score=(quality_assessment.quality_score if quality_assessment else None),
            quality_summary=(quality_assessment.quality_summary if quality_assessment else None),
            quality_assessment_source=(quality_assessment.quality_assessment_source if quality_assessment else 'text_signal'),
            quality_signals=(quality_assessment.quality_signals if quality_assessment else []),
            source_channel='whatsapp',
            raw_message=message_text,
            image_url=public_image_url,
            freshness_label='AI photo checked' if quality_assessment else 'Fresh today',
        )

    def assess_produce_image(
        self,
        *,
        image_bytes: bytes | None,
        image_mime_type: str | None,
        image_url: str | None = None,
        product_hint: str | None = None,
    ) -> ProduceQualityAssessment | None:
        if not image_bytes:
            return None
        return ProduceQualityAssessment(
            quality_grade='premium',
            quality_score=92,
            quality_summary='Bright color with minimal visible blemishes.',
            quality_assessment_source='ai_visual',
            quality_signals=['bright color', 'minimal blemishes'],
            detected_product_name='Tomato',
            detected_category='vegetables',
            estimated_visible_count=60,
        )

    def build_seller_dashboard(self, seller_id: str):  # pragma: no cover - not used in these tests
        return None


class RecordingWhatsApp:
    def __init__(self, *, list_sent: bool = True) -> None:
        self.list_sent = list_sent
        self.list_messages: list[dict[str, Any]] = []
        self.text_messages: list[dict[str, str]] = []
        self.button_messages: list[dict[str, Any]] = []

    def send_list_message(
        self,
        *,
        to: str,
        body: str,
        button_text: str,
        sections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self.list_messages.append(
            {
                'to': to,
                'body': body,
                'button_text': button_text,
                'sections': sections,
            }
        )
        return {'sent': self.list_sent}

    def send_text_message(self, to: str, body: str) -> dict[str, Any]:
        self.text_messages.append({'to': to, 'body': body})
        return {'sent': True}

    def send_reply_buttons(self, *, to: str, body: str, buttons: list[dict[str, str]]) -> dict[str, Any]:
        self.button_messages.append({'to': to, 'body': body, 'buttons': buttons})
        return {'sent': True}


class CapturingWhatsAppService(WhatsAppService):
    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None

    def _post_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.payload = payload
        return {'sent': True}


class InMemorySellerStore:
    def __init__(self) -> None:
        self.profile = SellerProfile(
            seller_id='919971497076',
            seller_name='Manya',
            store_name='Manya Store',
            preferred_language='hi',
            default_pickup_location='Shanti Nagar',
            registration_status='active',
        )
        self.session: SellerSession | None = None
        self.orders: list[Order] = []
        self.ledger_entries: list[Any] = []

    def get_seller_profile(self, seller_id: str) -> SellerProfile | None:
        return self.profile if seller_id == self.profile.seller_id else None

    def save_seller_profile(self, profile: SellerProfile) -> None:
        self.profile = profile

    def get_seller_session(self, seller_id: str) -> SellerSession | None:
        return self.session if self.session and seller_id == self.session.seller_id else None

    def save_seller_session(self, session: SellerSession) -> None:
        self.session = session

    def clear_seller_session(self, seller_id: str) -> None:
        if self.session and seller_id == self.session.seller_id:
            self.session = None

    def list_orders(self) -> list[Order]:
        return self.orders

    def get_order(self, order_id: str) -> Order | None:
        for order in self.orders:
            if order.id == order_id:
                return order
        return None

    def save_order(self, order: Order) -> Order:
        self.orders = [item for item in self.orders if item.id != order.id]
        self.orders.append(order)
        return order

    def list_ledger_entries(self) -> list[Any]:
        return self.ledger_entries

    def save_ledger_entry(self, entry: Any) -> Any:
        self.ledger_entries = [item for item in self.ledger_entries if item.id != entry.id]
        self.ledger_entries.append(entry)
        return entry

    def save_insight(self, insight: Any) -> Any:
        return insight

    def claim_whatsapp_message_fingerprint(self, fingerprint: str, window_seconds: int = 90) -> bool:
        return True

    def mark_whatsapp_message_fingerprint_processed(self, fingerprint: str) -> None:
        return None

    def release_whatsapp_message_fingerprint(self, fingerprint: str) -> None:
        return None


class OrderResponseMarketplace(StubMarketplace):
    def __init__(self, store: InMemorySellerStore) -> None:
        super().__init__()
        self.store = store

    def respond_to_order(self, order_id: str, decision: str) -> Order:
        order = self.store.get_order(order_id)
        assert order is not None
        order.status = 'accepted' if decision == 'accept' else 'rejected'
        return self.store.save_order(order)


class ListingSlotMarketplace(StubMarketplace):
    def __init__(self) -> None:
        super().__init__()
        self.extractor = ExtractionService()
        self.last_message_text: str | None = None

    def create_listing_from_message(
        self,
        *,
        seller_id: str,
        seller_name: str,
        message_text: str,
        image_url: str | None,
        source_channel: str = 'api',
        default_pickup_location: str | None = None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        quality_assessment: ProduceQualityAssessment | None = None,
    ) -> Listing:
        self.last_message_text = message_text
        return super().create_listing_from_message(
            seller_id=seller_id,
            seller_name=seller_name,
            message_text=message_text,
            image_url=image_url,
            source_channel=source_channel,
            default_pickup_location=default_pickup_location,
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            quality_assessment=quality_assessment,
        )


def _seed_active_seller(store: JsonStore, **overrides) -> None:
    payload = {
        'seller_id': '919971497076',
        'seller_name': 'Manya',
        'store_name': 'Manya Store',
        'preferred_language': 'hi',
        'default_pickup_location': 'Shanti Nagar',
        'registration_status': 'active',
    }
    payload.update(overrides)
    profile = SellerProfile(**payload)
    store.save_seller_profile(profile)


def _row_count(sections: list[dict[str, Any]]) -> int:
    return sum(len(section.get('rows') or []) for section in sections)


def test_active_seller_hi_menu_stays_within_whatsapp_row_limit() -> None:
    store = InMemorySellerStore()
    marketplace = StubMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='hi',
        image_url=None,
    )

    assert result == {'ok': True, 'handled': 'seller_menu'}
    assert len(whatsapp.list_messages) == 1
    assert _row_count(whatsapp.list_messages[0]['sections']) == MAX_LIST_ROWS
    row_ids = [
        row['id']
        for section in whatsapp.list_messages[0]['sections']
        for row in section['rows']
    ]
    assert MENU_ACTION_ORDERS in row_ids
    assert MENU_ACTION_VERIFICATION in row_ids
    assert whatsapp.text_messages == []


def test_verification_tools_menu_keeps_secondary_actions_under_row_limit() -> None:
    store = InMemorySellerStore()
    marketplace = StubMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='VERIFY',
        image_url=None,
    )

    assert result == {'ok': True, 'handled': 'seller_verification_menu'}
    assert len(whatsapp.list_messages) == 1
    assert _row_count(whatsapp.list_messages[0]['sections']) < MAX_LIST_ROWS
    row_ids = [
        row['id']
        for section in whatsapp.list_messages[0]['sections']
        for row in section['rows']
    ]
    assert 'menu_update_verification_method' in row_ids
    assert 'menu_update_location' in row_ids


def test_hindi_language_update_uses_devanagari_copy() -> None:
    store = InMemorySellerStore()
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    store.save_seller_session(SellerSession(seller_id='919971497076', state='awaiting_language_update'))
    marketplace = StubMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='हिंदी',
        image_url=None,
        interaction_id='lang_hi',
    )

    assert result == {'ok': True, 'handled': 'seller_language_updated'}
    assert store.profile.preferred_language == 'hi'
    assert whatsapp.text_messages[0]['body'] == 'आपकी भाषा अपडेट हो गई है।'


def test_incomplete_registration_greeting_restarts_at_language() -> None:
    store = InMemorySellerStore()
    store.profile.registration_status = 'verification_pending'
    store.profile.store_name = 'Bad Store'
    store.profile.default_pickup_location = 'Menu'
    store.profile.seller_type = 'farmer'
    store.profile.verification_method = 'farmer_registry'
    store.profile.verification_number = '12345678'
    store.profile.verification_proof_url = 'proof-id'
    store.save_seller_session(SellerSession(seller_id='919971497076', state='awaiting_seller_type'))
    marketplace = StubMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='hi',
        image_url=None,
    )

    assert result == {'ok': True, 'handled': 'seller_onboarding_language'}
    assert store.profile.registration_status == 'pending'
    assert store.profile.store_name is None
    assert store.profile.default_pickup_location is None
    assert store.profile.seller_type is None
    assert store.profile.verification_method is None
    assert store.profile.verification_number is None
    assert store.profile.verification_proof_url is None
    assert store.session is not None
    assert store.session.state == 'awaiting_language'
    assert whatsapp.button_messages
    assert [button['id'] for button in whatsapp.button_messages[-1]['buttons']] == ['lang_hi', 'lang_en']


def test_language_prompt_does_not_treat_hi_greeting_as_hindi_selection() -> None:
    store = InMemorySellerStore()
    store.profile.registration_status = 'pending'
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    store.save_seller_session(SellerSession(seller_id='919971497076', state='awaiting_language'))
    marketplace = StubMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='hi',
        image_url=None,
    )

    assert result == {'ok': True, 'handled': 'seller_onboarding_language'}
    assert store.profile.preferred_language == 'en'
    assert store.session is not None
    assert store.session.state == 'awaiting_language'
    assert whatsapp.text_messages == []
    assert whatsapp.button_messages


def test_stale_language_session_recovers_verification_number_step() -> None:
    store = InMemorySellerStore()
    store.profile.registration_status = 'verification_pending'
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    store.profile.seller_type = 'fpo'
    store.profile.verification_method = 'fpo_certificate'
    store.save_seller_session(SellerSession(seller_id='919971497076', state='awaiting_language'))
    marketplace = StubMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='123456',
        image_url=None,
    )

    assert result == {'ok': True, 'handled': 'seller_verification_proof'}
    assert store.profile.seller_type == 'fpo'
    assert store.profile.verification_method == 'fpo_certificate'
    assert store.profile.verification_number == '123456'
    assert store.session is not None
    assert store.session.state == 'awaiting_verification_proof'
    assert 'photo or PDF screenshot' in whatsapp.text_messages[-1]['body']


def test_partial_listing_with_product_and_quantity_asks_for_price_then_creates_listing() -> None:
    store = InMemorySellerStore()
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    store.save_seller_session(SellerSession(seller_id='919971497076', state='awaiting_listing_message'))
    marketplace = ListingSlotMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='40 kilo baingan',
        image_url=None,
    )

    assert result == {'ok': True, 'handled': 'seller_listing_slot_prompt'}
    assert store.session is not None
    assert store.session.state == 'awaiting_listing_price'
    assert store.session.draft_message == '40 kilo baingan'
    assert whatsapp.text_messages[-1]['body'] == 'What price per kg for 40 kg Brinjal? Example: 30 rupees kilo.'

    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='30',
        image_url=None,
    )

    assert result['ok'] is True
    assert result['handled'] == 'listing_created'
    assert store.session is None
    assert marketplace.last_message_text == '40 kilo baingan 30 rupees kilo'


def test_voice_listing_requires_review_before_going_live() -> None:
    store = InMemorySellerStore()
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    marketplace = ListingSlotMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='20 kilo potatao 1 rupees kilo',
        image_url=None,
        capture_mode='voice_note',
    )

    assert result == {'ok': True, 'handled': 'seller_listing_review'}
    assert marketplace.calls == 0
    assert store.session is not None
    assert store.session.state == 'awaiting_listing_confirmation'
    assert store.session.draft_capture_mode == 'voice_note'
    assert 'Price: Rs 1/kg' in whatsapp.button_messages[-1]['body']
    assert [button['id'] for button in whatsapp.button_messages[-1]['buttons']] == [
        'listing_confirm_live',
        'listing_edit',
    ]

    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Edit',
        image_url=None,
        interaction_id='listing_edit',
    )

    assert result == {'ok': True, 'handled': 'seller_listing_edit_prompt'}
    assert store.session is not None
    assert store.session.state == 'awaiting_listing_message'
    assert store.session.draft_message == '20 kilo potatao 1 rupees kilo'
    assert store.session.draft_capture_mode == 'voice_note'

    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='20 kilo potato 30 rupees kilo',
        image_url=None,
    )

    assert result == {'ok': True, 'handled': 'seller_listing_review'}
    assert marketplace.calls == 0
    assert store.session is not None
    assert store.session.state == 'awaiting_listing_confirmation'
    assert 'Price: Rs 30/kg' in whatsapp.button_messages[-1]['body']

    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Make live',
        image_url=None,
        interaction_id='listing_confirm_live',
    )

    assert result['ok'] is True
    assert result['handled'] == 'listing_created'
    assert marketplace.calls == 1
    assert store.session is None
    assert marketplace.last_message_text == '20 kilo Potato, 30 rupees kilo'


def test_voice_listing_edit_can_change_only_pickup_location() -> None:
    store = InMemorySellerStore()
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    marketplace = ListingSlotMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='20 kilo onion 50 rupees kilo okhla pickup',
        image_url=None,
        capture_mode='voice_note',
    )

    assert result == {'ok': True, 'handled': 'seller_listing_review'}
    assert 'Pickup: Okhla' in whatsapp.button_messages[-1]['body']

    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Edit',
        image_url=None,
        interaction_id='listing_edit',
    )

    assert result == {'ok': True, 'handled': 'seller_listing_edit_prompt'}
    assert store.session is not None
    assert store.session.draft_message == '20 kilo onion 50 rupees kilo okhla pickup'

    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Nehru Place',
        image_url=None,
        capture_mode='voice_note',
    )

    assert result == {'ok': True, 'handled': 'seller_listing_review'}
    assert marketplace.calls == 0
    assert store.session is not None
    assert store.session.state == 'awaiting_listing_confirmation'
    assert 'Pickup: Nehru Place' in whatsapp.button_messages[-1]['body']

    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Make live',
        image_url=None,
        interaction_id='listing_confirm_live',
    )

    assert result['ok'] is True
    assert result['handled'] == 'listing_created'
    assert marketplace.calls == 1
    assert marketplace.last_message_text == '20 kilo Onion, 50 rupees kilo, Nehru Place pickup'


def test_image_only_listing_prompt_preserves_visual_grade_until_listing_details_arrive() -> None:
    store = InMemorySellerStore()
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    marketplace = ListingSlotMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='',
        image_url='media-produce-123',
        image_bytes=b'fake-image',
        image_mime_type='image/jpeg',
    )

    assert result == {'ok': True, 'handled': 'seller_listing_prompt'}
    assert store.session is not None
    assert store.session.state == 'awaiting_listing_message'
    assert store.session.draft_quality_grade == 'premium'
    assert store.session.draft_quality_score == 92
    assert store.session.draft_detected_product_name == 'Tomato'
    assert store.session.draft_estimated_visible_count == 60
    assert 'I detected Tomato.' in whatsapp.text_messages[-1]['body']
    assert 'AI visual check: Premium (92/100).' in whatsapp.text_messages[-1]['body']
    assert 'Send kg and price' in whatsapp.text_messages[-1]['body']

    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='20 kilo 30 rupees kilo',
        image_url=None,
    )

    assert result['ok'] is True
    assert result['handled'] == 'listing_created'
    assert store.session is None
    assert marketplace.last_message_text == 'Tomato 20 kilo 30 rupees kilo'
    assert marketplace.last_quality_assessment is not None
    assert marketplace.last_quality_assessment.quality_grade == 'premium'
    assert marketplace.last_quality_assessment.quality_score == 92
    assert marketplace.last_quality_assessment.detected_product_name == 'Tomato'


def test_yes_accepts_latest_pending_order() -> None:
    store = InMemorySellerStore()
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    now = datetime.utcnow()
    older_order = Order(
        listing_id='lst_old',
        seller_id='919971497076',
        seller_name='Manya',
        product_name='Potato',
        buyer_name='Older Buyer',
        buyer_type='restaurant',
        quantity_kg=5,
        pickup_time='Today 4 PM',
        unit_price=40,
        total_price=200,
        created_at=now - timedelta(minutes=5),
    )
    latest_order = Order(
        listing_id='lst_new',
        seller_id='919971497076',
        seller_name='Manya',
        product_name='Tomato',
        buyer_name='FreshBite Restaurant',
        buyer_type='restaurant',
        quantity_kg=20,
        pickup_time='Today 5 PM',
        unit_price=40,
        total_price=800,
        created_at=now,
    )
    store.orders = [older_order, latest_order]
    marketplace = OrderResponseMarketplace(store)
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Yes',
        image_url=None,
    )

    assert result == {'ok': True, 'handled': 'seller_order_accepted'}
    assert latest_order.status == 'accepted'
    assert older_order.status == 'pending'
    assert whatsapp.text_messages[-1]['body'] == 'Order accepted. 20 kg Tomato, pickup Today 5 PM.'


def test_yes_with_order_number_accepts_selected_recent_order() -> None:
    store = InMemorySellerStore()
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    now = datetime.utcnow()
    newest_order = Order(
        listing_id='lst_new',
        seller_id='919971497076',
        seller_name='Manya',
        product_name='Spinach',
        buyer_name='Manya Restaurant',
        buyer_type='restaurant',
        quantity_kg=20,
        pickup_time='Today 5 PM',
        unit_price=40,
        total_price=800,
        created_at=now,
    )
    second_order = Order(
        listing_id='lst_old',
        seller_id='919971497076',
        seller_name='Manya',
        product_name='Potato',
        buyer_name='FreshBite Restaurant',
        buyer_type='restaurant',
        quantity_kg=10,
        pickup_time='Today 5 PM',
        unit_price=40,
        total_price=400,
        created_at=now - timedelta(minutes=5),
    )
    store.orders = [second_order, newest_order]
    marketplace = OrderResponseMarketplace(store)
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='YES 2',
        image_url=None,
    )

    assert result == {'ok': True, 'handled': 'seller_order_accepted'}
    assert newest_order.status == 'pending'
    assert second_order.status == 'accepted'
    assert whatsapp.text_messages[-1]['body'] == 'Order #2 accepted. 10 kg Potato, pickup Today 5 PM.'


def test_no_rejects_pending_order() -> None:
    store = InMemorySellerStore()
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    order = Order(
        listing_id='lst_new',
        seller_id='919971497076',
        seller_name='Manya',
        product_name='Tomato',
        buyer_name='FreshBite Restaurant',
        buyer_type='restaurant',
        quantity_kg=20,
        pickup_time='Today 5 PM',
        unit_price=40,
        total_price=800,
    )
    store.orders = [order]
    marketplace = OrderResponseMarketplace(store)
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='No',
        image_url=None,
    )

    assert result == {'ok': True, 'handled': 'seller_order_rejected'}
    assert order.status == 'rejected'
    assert whatsapp.text_messages[-1]['body'] == 'Order rejected. 20 kg Tomato, pickup Today 5 PM.'


def test_order_button_reply_accepts_specific_order() -> None:
    store = InMemorySellerStore()
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    now = datetime.utcnow()
    first_order = Order(
        listing_id='lst_first',
        seller_id='919971497076',
        seller_name='Manya',
        product_name='Potato',
        buyer_name='FreshBite Restaurant',
        buyer_type='restaurant',
        quantity_kg=10,
        pickup_time='Today 5 PM',
        unit_price=40,
        total_price=400,
        created_at=now - timedelta(minutes=5),
    )
    latest_order = Order(
        listing_id='lst_latest',
        seller_id='919971497076',
        seller_name='Manya',
        product_name='Tomato',
        buyer_name='Manya Restaurant',
        buyer_type='restaurant',
        quantity_kg=20,
        pickup_time='Today 6 PM',
        unit_price=40,
        total_price=800,
        created_at=now,
    )
    store.orders = [first_order, latest_order]
    marketplace = OrderResponseMarketplace(store)
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Accept',
        image_url=None,
        interaction_id=f'order_accept:{first_order.id}',
    )

    assert result == {'ok': True, 'handled': 'seller_order_accepted'}
    assert first_order.status == 'accepted'
    assert latest_order.status == 'pending'
    assert whatsapp.text_messages[-1]['body'] == 'Order accepted. 10 kg Potato, pickup Today 5 PM.'


def test_orders_menu_shows_recent_orders() -> None:
    store = InMemorySellerStore()
    store.profile.preferred_language = 'en'  # type: ignore[assignment]
    now = datetime.utcnow()
    store.orders = [
        Order(
            listing_id='lst_new',
            seller_id='919971497076',
            seller_name='Manya',
            product_name='Tomato',
            buyer_name='FreshBite Restaurant',
            buyer_type='restaurant',
            quantity_kg=20,
            pickup_time='Today 5 PM',
            unit_price=40,
            total_price=800,
            created_at=now,
        ),
        Order(
            listing_id='lst_old',
            seller_id='919971497076',
            seller_name='Manya',
            product_name='Potato',
            buyer_name='Older Buyer',
            buyer_type='restaurant',
            quantity_kg=5,
            pickup_time='Today 4 PM',
            unit_price=40,
            total_price=200,
            status='accepted',
            created_at=now - timedelta(minutes=5),
        )
    ]
    marketplace = OrderResponseMarketplace(store)
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='ORDERS',
        image_url=None,
    )

    assert result == {'ok': True, 'handled': 'seller_orders'}
    assert whatsapp.text_messages == []
    assert whatsapp.list_messages[-1]['button_text'] == 'Manage orders'
    assert whatsapp.list_messages[-1]['body'] == (
        'Your recent orders:\n'
        '- 1. PENDING: 20 kg Tomato, FreshBite Restaurant, pickup Today 5 PM. Reply YES 1 or NO 1\n'
        '- 2. ACCEPTED: 5 kg Potato, Older Buyer, pickup Today 4 PM'
    )
    rows = whatsapp.list_messages[-1]['sections'][0]['rows']
    assert rows == [
        {
            'id': f'order_accept:{store.orders[0].id}',
            'title': 'Accept 1',
            'description': '20 kg Tomato, FreshBite Restaurant, pickup Today 5 PM',
        },
        {
            'id': f'order_reject:{store.orders[0].id}',
            'title': 'Reject 1',
            'description': '20 kg Tomato, FreshBite Restaurant, pickup Today 5 PM',
        },
    ]


def test_seller_type_update_returns_to_menu() -> None:
    store = InMemorySellerStore()
    store.profile.seller_type = 'farmer'
    store.profile.verification_method = 'farmer_registry'
    store.profile.verification_number = 'OLD-123'
    store.save_seller_session(SellerSession(seller_id='919971497076', state='awaiting_seller_type_update'))
    marketplace = StubMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Trader',
        image_url=None,
        interaction_id='seller_trader',
    )

    assert result == {'ok': True, 'handled': 'seller_type_updated'}
    assert store.profile.seller_type == 'trader'
    assert store.profile.verification_method == 'farmer_registry'
    assert store.profile.verification_number == 'OLD-123'
    assert store.session is None
    assert whatsapp.button_messages == []
    assert whatsapp.list_messages


def test_verification_method_update_returns_to_menu() -> None:
    store = InMemorySellerStore()
    store.profile.seller_type = 'aggregator'
    store.profile.verification_method = 'fssai'
    store.profile.verification_number = 'OLD-123'
    store.save_seller_session(SellerSession(seller_id='919971497076', state='awaiting_verification_method_update'))
    marketplace = StubMarketplace()
    whatsapp = RecordingWhatsApp()

    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='eNAM',
        image_url=None,
        interaction_id='verify_enam',
    )

    assert result == {'ok': True, 'handled': 'seller_verification_method_updated'}
    assert store.profile.verification_method == 'enam'
    assert store.profile.verification_number == 'OLD-123'
    assert store.session is None
    assert len(whatsapp.text_messages) == 1
    assert whatsapp.list_messages


def test_whatsapp_list_payload_is_sanitized_to_platform_limits() -> None:
    whatsapp = CapturingWhatsAppService()
    rows = [
        {
            'id': f'row-{index}',
            'title': f'Long row title number {index}',
            'description': 'x' * 100,
        }
        for index in range(12)
    ]

    result = whatsapp.send_list_message(
        to='919971497076',
        body='Menu',
        button_text='Open menu',
        sections=[{'title': 'A very long section title', 'rows': rows}],
    )

    assert result == {'sent': True}
    assert whatsapp.payload is not None
    sections = whatsapp.payload['interactive']['action']['sections']
    assert _row_count(sections) == MAX_LIST_ROWS
    assert len(sections[0]['title']) <= 24
    assert all(len(row['title']) <= 24 for row in sections[0]['rows'])
    assert all(len(row['description']) <= 72 for row in sections[0]['rows'])


def test_whatsapp_webhook_starts_onboarding_for_new_seller(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = StubMarketplace()

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-onboarding',
                        'type': 'text',
                        'text': {'body': 'Hi'},
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)
        response = client.post('/api/webhooks/whatsapp/inbound', json=payload)

        assert response.status_code == 200
        assert response.json() == {'ok': True, 'handled': 'seller_onboarding_language'}
        assert marketplace.calls == 0
        assert store.get_seller_profile('919971497076') is not None
        assert store.get_seller_session('919971497076') is not None
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_dedupes_same_message_id(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = StubMarketplace()
    _seed_active_seller(store)

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-123',
                        'type': 'text',
                        'text': {'body': 'Aaj 50 kilo tamatar hai, 28 rupay kilo, Laxmi Nagar pickup'},
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)

        first = client.post('/api/webhooks/whatsapp/inbound', json=payload)
        second = client.post('/api/webhooks/whatsapp/inbound', json=payload)

        assert first.status_code == 200
        assert first.json()['ok'] is True
        assert second.status_code == 200
        assert second.json() == {'ok': True, 'ignored': True, 'reason': 'duplicate_message'}
        assert marketplace.calls == 1
        assert store.has_processed_whatsapp_message('wamid.test-123') is True
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_dedupes_same_text_with_different_message_ids(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = StubMarketplace()
    _seed_active_seller(store)

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    first_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-201',
                        'type': 'text',
                        'text': {'body': 'Aaj 50 kilo tamatar hai, 28 rupay kilo, Laxmi Nagar pickup'},
                    }],
                },
            }],
        }],
    }
    second_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-202',
                        'type': 'text',
                        'text': {'body': 'Aaj 50 kilo tamatar hai, 28 rupay kilo, Laxmi Nagar pickup'},
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)

        first = client.post('/api/webhooks/whatsapp/inbound', json=first_payload)
        second = client.post('/api/webhooks/whatsapp/inbound', json=second_payload)

        assert first.status_code == 200
        assert first.json()['ok'] is True
        assert second.status_code == 200
        assert second.json() == {'ok': True, 'ignored': True, 'reason': 'duplicate_text_fingerprint'}
        assert marketplace.calls == 1
        assert store.has_processed_whatsapp_message('wamid.test-202') is True
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_transcribes_audio_messages_before_processing(tmp_path: Path, monkeypatch) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = ListingSlotMarketplace()
    _seed_active_seller(store)

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    audio_calls: list[str] = []
    transcript_calls: list[tuple[bytes, str]] = []

    def fake_fetch_media_bytes(self, media_id: str) -> tuple[bytes | None, str | None]:
        audio_calls.append(media_id)
        return b'fake-audio', 'audio/ogg; codecs=opus'

    def fake_transcribe_bytes(self, audio_bytes: bytes, mime_type: str = 'audio/ogg') -> str | None:
        transcript_calls.append((audio_bytes, mime_type))
        return 'Aaj 20 kilo tamatar hai, 30 rupay kilo, Shanti Nagar pickup'

    def fake_post_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {'sent': True, 'payload': payload}

    monkeypatch.setattr(WhatsAppService, 'fetch_media_bytes', fake_fetch_media_bytes)
    monkeypatch.setattr('app.api.routes.SpeechService.transcribe_bytes', fake_transcribe_bytes)
    monkeypatch.setattr(WhatsAppService, '_post_message', fake_post_message)

    payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.audio-123',
                        'type': 'audio',
                        'audio': {'id': 'media-audio-123'},
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)

        response = client.post('/api/webhooks/whatsapp/inbound', json=payload)

        assert response.status_code == 200
        assert response.json()['ok'] is True
        assert audio_calls == ['media-audio-123']
        assert transcript_calls == [(b'fake-audio', 'audio/ogg; codecs=opus')]
        assert marketplace.calls == 1
        assert marketplace.last_message_text == 'Aaj 20 kilo tamatar hai, 30 rupay kilo, Shanti Nagar pickup'
        assert store.has_processed_whatsapp_message('wamid.audio-123') is True
    finally:
        app.dependency_overrides.clear()


def test_seller_can_request_khata_summary_over_whatsapp(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    _seed_active_seller(store, preferred_language='en')
    marketplace = MarketplaceService(store)
    whatsapp = RecordingWhatsApp()
    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)

    recorded = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Raju bought 10 kg tomatoes for Rs 250 today, but still owes me Rs 50.',
        image_url=None,
        capture_mode='voice_note',
    )

    assert recorded == {'ok': True, 'handled': 'seller_ledger_recorded'}
    entries = store.list_ledger_entries()
    assert len(entries) == 1
    assert entries[0].capture_mode == 'voice_note'
    assert entries[0].amount_due == 50.0

    summary = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='KHATA',
        image_url=None,
    )

    assert summary == {'ok': True, 'handled': 'seller_ledger'}
    assert 'Khata summary' in whatsapp.text_messages[-1]['body']
    assert 'Outstanding: Rs 50' in whatsapp.text_messages[-1]['body']
    assert 'Raju: Tomato, total Rs 250, due Rs 50' in whatsapp.text_messages[-1]['body']


def test_khata_summary_reduces_outstanding_after_payment_note(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    _seed_active_seller(store, preferred_language='en')
    marketplace = MarketplaceService(store)
    whatsapp = RecordingWhatsApp()
    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)

    first = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Raju bought 10 kg tomatoes for Rs 250 today, but still owes me Rs 50.',
        image_url=None,
        capture_mode='voice_note',
    )
    second = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Raju paid Rs 50 today for the earlier tomato balance.',
        image_url=None,
    )
    summary = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='ledger',
        image_url=None,
    )

    assert first == {'ok': True, 'handled': 'seller_ledger_recorded'}
    assert second == {'ok': True, 'handled': 'seller_ledger_recorded'}
    assert summary == {'ok': True, 'handled': 'seller_ledger'}
    assert 'Outstanding: Rs 0' in whatsapp.text_messages[-1]['body']
    assert 'Collected: Rs 250' in whatsapp.text_messages[-1]['body']
    assert 'Buyers with dues: 0' in whatsapp.text_messages[-1]['body']


def test_payment_note_keeps_buyer_name_without_auxiliary_verbs(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    _seed_active_seller(store, preferred_language='en')
    marketplace = MarketplaceService(store)
    whatsapp = RecordingWhatsApp()
    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)

    sale_result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Raju bought 10 kg tomatoes for Rs 250 today, but still owes me Rs 100.',
        image_url=None,
    )
    payment_result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Manya',
        message_text='Raju has paid me 100 rupees.',
        image_url=None,
    )
    ledger = marketplace.build_seller_ledger('919971497076')

    assert sale_result == {'ok': True, 'handled': 'seller_ledger_recorded'}
    assert payment_result == {'ok': True, 'handled': 'seller_ledger_recorded'}
    assert ledger is not None
    assert ledger.items[0].buyer_name == 'Raju'
    assert ledger.summary.total_outstanding_amount == 0
    assert ledger.summary.buyers_with_balance == 0


def test_seller_ledger_reprices_sale_entries_from_latest_listing_price(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    _seed_active_seller(store, preferred_language='en')
    marketplace = MarketplaceService(store)
    store.save_listing(Listing(
        seller_id='919971497076',
        seller_name='Manya',
        product_name='Potato',
        category='vegetables',
        quantity_kg=40,
        available_kg=40,
        price_per_kg=15,
        pickup_location='Laxmi Nagar',
    ))
    store.save_ledger_entry(LedgerEntry(
        seller_id='919971497076',
        buyer_name='Raju',
        entry_kind='sale',
        product_name='Potato',
        quantity_kg=10,
        total_amount=100,
        amount_paid=0,
        amount_due=100,
        balance_delta=100,
        summary='Raju bought 10 kg Potato. Total Rs 100, due Rs 100.',
    ))

    ledger = marketplace.build_seller_ledger('919971497076')

    assert ledger is not None
    assert ledger.summary.total_outstanding_amount == 150
    assert ledger.items[0].total_amount == 150
    assert ledger.items[0].amount_due == 150
    assert 'Total Rs 150' in ledger.items[0].summary


def test_whatsapp_webhook_records_voice_ledger_entry_and_exposes_dashboard_data(tmp_path: Path, monkeypatch) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = MarketplaceService(store)
    _seed_active_seller(store, preferred_language='en')

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    def fake_fetch_media_bytes(self, media_id: str) -> tuple[bytes | None, str | None]:
        assert media_id == 'media-audio-ledger'
        return b'fake-ledger-audio', 'audio/ogg; codecs=opus'

    def fake_transcribe_bytes(self, audio_bytes: bytes, mime_type: str = 'audio/ogg') -> str | None:
        assert audio_bytes == b'fake-ledger-audio'
        assert mime_type == 'audio/ogg; codecs=opus'
        return 'Raju bought 10 kg tomatoes for Rs 250 today, but still owes me Rs 50.'

    def fake_post_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {'sent': True, 'payload': payload}

    monkeypatch.setattr(WhatsAppService, 'fetch_media_bytes', fake_fetch_media_bytes)
    monkeypatch.setattr('app.api.routes.SpeechService.transcribe_bytes', fake_transcribe_bytes)
    monkeypatch.setattr(WhatsAppService, '_post_message', fake_post_message)

    payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.audio-ledger-1',
                        'type': 'audio',
                        'audio': {'id': 'media-audio-ledger'},
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)

        response = client.post('/api/webhooks/whatsapp/inbound', json=payload)
        ledger_response = client.get('/api/sellers/919971497076/ledger')
        dashboard_response = client.get('/api/sellers/919971497076/dashboard')

        assert response.status_code == 200
        assert response.json() == {'ok': True, 'handled': 'seller_ledger_recorded'}

        entries = store.list_ledger_entries()
        assert len(entries) == 1
        entry = entries[0]
        assert entry.buyer_name == 'Raju'
        assert entry.capture_mode == 'voice_note'
        assert entry.total_amount == 250.0
        assert entry.amount_due == 50.0

        assert ledger_response.status_code == 200
        assert ledger_response.json()['summary']['total_entries'] == 1
        assert ledger_response.json()['summary']['total_outstanding_amount'] == 50.0
        assert ledger_response.json()['items'][0]['capture_mode'] == 'voice_note'

        assert dashboard_response.status_code == 200
        assert dashboard_response.json()['ledger_entries_count'] == 1
        assert dashboard_response.json()['ledger_outstanding_amount'] == 50.0
        assert dashboard_response.json()['recent_ledger_entries'][0]['buyer_name'] == 'Raju'
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_applies_visual_grade_to_image_listing(tmp_path: Path, monkeypatch) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = ListingSlotMarketplace()
    _seed_active_seller(store)

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    def fake_fetch_media_bytes(self, media_id: str) -> tuple[bytes | None, str | None]:
        assert media_id == 'media-produce-123'
        return b'fake-image', 'image/jpeg'

    def fake_post_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {'sent': True, 'payload': payload}

    monkeypatch.setattr(WhatsAppService, 'fetch_media_bytes', fake_fetch_media_bytes)
    monkeypatch.setattr(WhatsAppService, '_post_message', fake_post_message)

    payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.image-123',
                        'type': 'image',
                        'image': {
                            'id': 'media-produce-123',
                            'caption': 'Aaj 20 kilo tamatar hai, 30 rupay kilo, Shanti Nagar pickup',
                        },
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)
        response = client.post('/api/webhooks/whatsapp/inbound', json=payload)

        assert response.status_code == 200
        assert response.json()['ok'] is True
        assert response.json()['handled'] == 'listing_created'
        assert response.json()['listing']['quality_assessment_source'] == 'ai_visual'
        assert response.json()['listing']['quality_grade'] == 'premium'
        assert response.json()['listing']['quality_score'] == 92
        assert marketplace.last_quality_assessment is not None
        assert marketplace.last_quality_assessment.quality_grade == 'premium'
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_accepts_image_only_verification_proof(tmp_path: Path, monkeypatch) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = StubMarketplace()
    store.save_seller_profile(
        SellerProfile(
            seller_id='919971497076',
            seller_name='Manya',
            store_name='Manya Store',
            preferred_language='hi',
            registration_status='verification_pending',
            verification_method='govt_id',
        )
    )
    store.save_seller_session(
        SellerSession(
            seller_id='919971497076',
            state='awaiting_verification_proof',
        )
    )

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    def fake_fetch_media_bytes(self, media_id: str) -> tuple[bytes | None, str | None]:
        assert media_id == 'media-proof-123'
        return b'proof-image', 'image/jpeg'

    def fake_post_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {'sent': True, 'payload': payload}

    monkeypatch.setattr(WhatsAppService, 'fetch_media_bytes', fake_fetch_media_bytes)
    monkeypatch.setattr(WhatsAppService, '_post_message', fake_post_message)

    payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-proof-image',
                        'type': 'image',
                        'image': {'id': 'media-proof-123'},
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)
        response = client.post('/api/webhooks/whatsapp/inbound', json=payload)

        assert response.status_code == 200
        assert response.json() == {'ok': True, 'handled': 'seller_verification_complete'}

        profile = store.get_seller_profile('919971497076')
        assert profile is not None
        assert profile.registration_status == 'active'
        assert profile.verification_status == 'verified'
        assert profile.verification_proof_url == 'media-proof-123'
        assert store.get_seller_session('919971497076') is None
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_updates_seller_name_after_registration(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = StubMarketplace()
    _seed_active_seller(store)

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    prompt_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-name-prompt',
                        'type': 'text',
                        'text': {'body': 'NAME'},
                    }],
                },
            }],
        }],
    }
    update_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-name-update',
                        'type': 'text',
                        'text': {'body': 'Shakti Traders'},
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)

        prompt = client.post('/api/webhooks/whatsapp/inbound', json=prompt_payload)
        update = client.post('/api/webhooks/whatsapp/inbound', json=update_payload)

        assert prompt.status_code == 200
        assert prompt.json() == {'ok': True, 'handled': 'seller_name_prompt'}
        assert update.status_code == 200
        assert update.json() == {'ok': True, 'handled': 'seller_name_updated'}

        profile = store.get_seller_profile('919971497076')
        assert profile is not None
        assert profile.seller_name == 'Shakti Traders'
        assert store.get_seller_session('919971497076') is None
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_updates_language_after_registration(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = StubMarketplace()
    _seed_active_seller(store)

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    prompt_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-language-prompt',
                        'type': 'text',
                        'text': {'body': 'LANGUAGE'},
                    }],
                },
            }],
        }],
    }
    update_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-language-update',
                        'type': 'interactive',
                        'interactive': {
                            'type': 'button_reply',
                            'button_reply': {
                                'id': 'lang_en',
                                'title': 'English',
                            },
                        },
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)

        prompt = client.post('/api/webhooks/whatsapp/inbound', json=prompt_payload)
        update = client.post('/api/webhooks/whatsapp/inbound', json=update_payload)

        assert prompt.status_code == 200
        assert prompt.json() == {'ok': True, 'handled': 'seller_language_prompt'}
        assert update.status_code == 200
        assert update.json() == {'ok': True, 'handled': 'seller_language_updated'}

        profile = store.get_seller_profile('919971497076')
        assert profile is not None
        assert profile.preferred_language == 'en'
        assert store.get_seller_session('919971497076') is None
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_updates_store_name_after_registration(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = StubMarketplace()
    _seed_active_seller(store)

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    prompt_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-store-prompt',
                        'type': 'text',
                        'text': {'body': 'STORE'},
                    }],
                },
            }],
        }],
    }
    update_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-store-update',
                        'type': 'text',
                        'text': {'body': 'Shakti Farm Collective'},
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)

        prompt = client.post('/api/webhooks/whatsapp/inbound', json=prompt_payload)
        update = client.post('/api/webhooks/whatsapp/inbound', json=update_payload)

        assert prompt.status_code == 200
        assert prompt.json() == {'ok': True, 'handled': 'seller_store_name_prompt'}
        assert update.status_code == 200
        assert update.json() == {'ok': True, 'handled': 'seller_store_name_updated'}

        profile = store.get_seller_profile('919971497076')
        assert profile is not None
        assert profile.store_name == 'Shakti Farm Collective'
        assert store.get_seller_session('919971497076') is None
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_updates_seller_type_after_registration(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = StubMarketplace()
    _seed_active_seller(store, seller_type='farmer')

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    prompt_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-type-prompt',
                        'type': 'text',
                        'text': {'body': 'TYPE'},
                    }],
                },
            }],
        }],
    }
    update_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-type-update',
                        'type': 'interactive',
                        'interactive': {
                            'type': 'list_reply',
                            'list_reply': {
                                'id': 'seller_trader',
                                'title': 'Trader',
                            },
                        },
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)

        prompt = client.post('/api/webhooks/whatsapp/inbound', json=prompt_payload)
        update = client.post('/api/webhooks/whatsapp/inbound', json=update_payload)

        assert prompt.status_code == 200
        assert prompt.json() == {'ok': True, 'handled': 'seller_type_update_prompt'}
        assert update.status_code == 200
        assert update.json() == {'ok': True, 'handled': 'seller_type_updated'}

        profile = store.get_seller_profile('919971497076')
        assert profile is not None
        assert profile.seller_type == 'trader'
        assert store.get_seller_session('919971497076') is None
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_updates_verification_method_after_registration(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = StubMarketplace()
    _seed_active_seller(store, seller_type='farmer', verification_method='govt_id')

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    prompt_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-verify-method-prompt',
                        'type': 'text',
                        'text': {'body': 'VERIFY METHOD'},
                    }],
                },
            }],
        }],
    }
    update_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-verify-method-update',
                        'type': 'interactive',
                        'interactive': {
                            'type': 'button_reply',
                            'button_reply': {
                                'id': 'verify_pm_kisan',
                                'title': 'PM-KISAN',
                            },
                        },
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)

        prompt = client.post('/api/webhooks/whatsapp/inbound', json=prompt_payload)
        update = client.post('/api/webhooks/whatsapp/inbound', json=update_payload)

        assert prompt.status_code == 200
        assert prompt.json() == {'ok': True, 'handled': 'seller_verification_method_update_prompt'}
        assert update.status_code == 200
        assert update.json() == {'ok': True, 'handled': 'seller_verification_method_updated'}

        profile = store.get_seller_profile('919971497076')
        assert profile is not None
        assert profile.verification_method == 'pm_kisan'
        assert store.get_seller_session('919971497076') is None
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_updates_verification_number_after_registration(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = StubMarketplace()
    _seed_active_seller(store, verification_number='OLD123')

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    prompt_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-verify-id-prompt',
                        'type': 'text',
                        'text': {'body': 'VERIFY ID'},
                    }],
                },
            }],
        }],
    }
    update_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-verify-id-update',
                        'type': 'text',
                        'text': {'body': 'FPO-REG-7788'},
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)

        prompt = client.post('/api/webhooks/whatsapp/inbound', json=prompt_payload)
        update = client.post('/api/webhooks/whatsapp/inbound', json=update_payload)

        assert prompt.status_code == 200
        assert prompt.json() == {'ok': True, 'handled': 'seller_verification_number_prompt'}
        assert update.status_code == 200
        assert update.json() == {'ok': True, 'handled': 'seller_verification_number_updated'}

        profile = store.get_seller_profile('919971497076')
        assert profile is not None
        assert profile.verification_number == 'FPO-REG-7788'
        assert store.get_seller_session('919971497076') is None
    finally:
        app.dependency_overrides.clear()


def test_whatsapp_webhook_updates_verification_proof_after_registration(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = StubMarketplace()
    _seed_active_seller(store, verification_status='manual_review', verification_proof_url='old-proof')

    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace

    prompt_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-verify-proof-prompt',
                        'type': 'text',
                        'text': {'body': 'VERIFY PROOF'},
                    }],
                },
            }],
        }],
    }
    update_payload = {
        'entry': [{
            'changes': [{
                'value': {
                    'contacts': [{
                        'profile': {'name': 'Manya'},
                    }],
                    'messages': [{
                        'from': '919971497076',
                        'id': 'wamid.test-verify-proof-update',
                        'type': 'image',
                        'image': {'id': 'proof-media-999'},
                    }],
                },
            }],
        }],
    }

    try:
        client = TestClient(app)

        prompt = client.post('/api/webhooks/whatsapp/inbound', json=prompt_payload)
        update = client.post('/api/webhooks/whatsapp/inbound', json=update_payload)

        assert prompt.status_code == 200
        assert prompt.json() == {'ok': True, 'handled': 'seller_verification_proof_prompt'}
        assert update.status_code == 200
        assert update.json() == {'ok': True, 'handled': 'seller_verification_proof_updated'}

        profile = store.get_seller_profile('919971497076')
        assert profile is not None
        assert profile.verification_proof_url == 'proof-media-999'
        assert profile.verification_status == 'verified'
        assert store.get_seller_session('919971497076') is None
    finally:
        app.dependency_overrides.clear()
