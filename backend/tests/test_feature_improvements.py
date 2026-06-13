from __future__ import annotations

from pathlib import Path
from typing import Any

from app.schemas import Delivery, DemandRequestCreate, Listing, NotificationRecord, ProduceQualityAssessment, SellerProfile
from app.services.market_price_service import MarketPriceService
from app.services.marketplace import MarketplaceService
from app.services.seller_flow import SellerFlowService
from app.services.store import JsonStore


class SilentWhatsApp:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def send_text_message(self, to: str, body: str) -> dict[str, Any]:
        self.messages.append({'to': to, 'body': body})
        return {'sent': True}

    def send_reply_buttons(self, *, to: str, body: str, buttons: list[dict[str, str]]) -> dict[str, Any]:
        self.messages.append({'to': to, 'body': body})
        return {'sent': True}

    def delivery_status(self, result: dict[str, Any]) -> str:
        return 'sent' if result.get('sent') else 'failed'


def _test_store(name: str) -> JsonStore:
    path = Path.cwd() / 'backend' / 'data' / f'{name}.json'
    if path.exists():
        path.unlink()
    return JsonStore(path)


def _configure_marketplace(store: JsonStore) -> MarketplaceService:
    marketplace = MarketplaceService(store)
    marketplace.whatsapp = SilentWhatsApp()  # type: ignore[assignment]
    marketplace.geo.resolve_distance = lambda **_: (10.0, 'haversine')  # type: ignore[method-assign]
    marketplace.geo.geocode = lambda location: {'pickup_location': location, 'latitude': 28.6, 'longitude': 77.2, 'place_id': 'demo'}  # type: ignore[method-assign]
    return marketplace


def _seed_listing(store: JsonStore) -> Listing:
    store.save_seller_profile(
        SellerProfile(
            seller_id='seller-1',
            seller_name='Shakti FPO',
            preferred_language='en',
            registration_status='active',
            default_pickup_location='Nashik Collection Hub',
            latitude=19.9975,
            longitude=73.7898,
        )
    )
    listing = Listing(
        seller_id='seller-1',
        seller_name='Shakti FPO',
        product_name='Tomato',
        quantity_kg=100,
        available_kg=100,
        price_per_kg=30,
        pickup_location='Nashik Collection Hub',
        quality_grade='premium',
        quality_assessment_source='text_signal',
        quality_signals=[],
        image_url='http://localhost:8000/media/listings/f8e86bbffaddeb22810dd7c3.jpg',
        image_source='seller_upload',
    )
    store.save_listing(listing)
    return listing


def _direct_order_payload(listing_id: str, quantity_kg: float = 10.0) -> Any:
    return type('OrderPayload', (), {
        'listing_id': listing_id,
        'buyer_name': 'Sunrise Kirana',
        'buyer_type': 'kirana',
        'quantity_kg': quantity_kg,
        'pickup_time': 'Today 5 PM',
        'phone': '9999999999',
        'buyer_phone': '9999999999',
        'delivery_mode': 'delivery',
        'delivery_address': 'Lajpat Nagar, Delhi',
    })()


def _advance_payload(next_status: str) -> Any:
    return type('AdvancePayload', (), {
        'next_status': next_status,
        'actor_role': 'ops',
        'actor_id': 'ops-demo',
    })()


def test_delivery_pricing_formula_and_caps() -> None:
    service = MarketplaceService(_test_store('test_feature_store'))
    breakdown = service.geo.estimate_delivery_breakdown(quantity_kg=10, distance_km=10, distance_source='haversine')
    assert breakdown.base_fee == 35
    assert breakdown.distance_fee == 120
    assert breakdown.weight_fee == 0
    assert breakdown.total_delivery_fee == 155

    heavy_breakdown = service.geo.estimate_delivery_breakdown(quantity_kg=30, distance_km=25, distance_source='haversine')
    assert heavy_breakdown.weight_fee == 15
    assert heavy_breakdown.total_delivery_fee <= 500


def test_place_order_uses_backend_delivery_estimate() -> None:
    store = _test_store('test_place_order')
    listing = _seed_listing(store)
    marketplace = _configure_marketplace(store)

    order = marketplace.place_order(payload=_direct_order_payload(listing.id, quantity_kg=20.0))

    assert order.delivery_fee == 162
    assert order.delivery_distance_km == 10.0
    assert order.buyer_total_payable == 762
    assert order.delivery_fee_breakdown is not None


def test_direct_delivery_orders_remain_visible_to_buyer_after_acceptance() -> None:
    store = _test_store('test_buyer_delivery_visibility')
    listing = _seed_listing(store)
    marketplace = _configure_marketplace(store)

    order = marketplace.place_order(payload=_direct_order_payload(listing.id))
    marketplace.respond_to_order(order.id, 'accept')
    deliveries = marketplace.list_deliveries(buyer_id='9999999999')

    assert len(deliveries) == 1
    assert deliveries[0].buyer_id == '9999999999'
    assert deliveries[0].order_id == order.id


def test_market_price_service_fallback_and_conversion() -> None:
    service = MarketPriceService()
    records = service.get_market_prices('tamatar')
    assert records
    first = records[0]
    assert first.product_name == 'Tomato'
    assert first.mandi_modal_price_per_kg == 28.0
    assert first.raw_unit == 'quintal'
    assert first.data_source == 'demo_fallback'


def test_notification_role_filter_and_mark_read() -> None:
    store = _test_store('test_notifications')
    store.add_notification(NotificationRecord(recipient_role='seller', recipient_id='seller-1', category='order', title='Seller note', text='seller').model_dump())
    store.add_notification(NotificationRecord(recipient_role='buyer', recipient_id='buyer-1', category='order', title='Buyer note', text='buyer').model_dump())

    seller_items = store.list_notifications(role='seller', recipient_id='seller-1')
    buyer_items = store.list_notifications(role='buyer', recipient_id='buyer-1')

    assert len(seller_items) == 1
    assert seller_items[0]['title'] == 'Seller note'
    assert len(buyer_items) == 1
    assert buyer_items[0]['title'] == 'Buyer note'

    updated = store.mark_notification_read(buyer_items[0]['id'])
    assert updated is not None
    assert updated['read_at'] is not None


def test_seller_whatsapp_bhav_command_returns_price_intelligence() -> None:
    store = _test_store('test_bhav_command')
    marketplace = MarketplaceService(store)
    whatsapp = SilentWhatsApp()
    flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)  # type: ignore[arg-type]
    store.save_seller_profile(
        SellerProfile(
            seller_id='919971497076',
            seller_name='Ramesh',
            preferred_language='hi',
            registration_status='active',
            default_pickup_location='Nashik',
        )
    )

    result = flow.handle_message(
        seller_id='919971497076',
        profile_name='Ramesh',
        message_text='bhav tamatar',
        image_url=None,
    )

    assert result['ok'] is True
    assert whatsapp.messages
    assert 'modal' in whatsapp.messages[-1]['body']


def test_listing_with_seller_image_preserves_image_source_and_quality_proof() -> None:
    store = _test_store('test_listing_seller_image')
    marketplace = _configure_marketplace(store)

    listing = marketplace.create_listing_from_message(
        seller_id='seller-1',
        seller_name='Shakti FPO',
        message_text='50 kilo tomato, 28 rupees kilo, Nashik pickup',
        image_url='http://localhost:8000/media/listings/f8e86bbffaddeb22810dd7c3.jpg',
        quality_assessment=ProduceQualityAssessment(
            quality_grade='premium',
            quality_score=92,
            quality_summary='Bright red and uniform tomatoes.',
            quality_assessment_source='ai_visual',
            quality_signals=['consistent color'],
            detected_product_name='Tomato',
            detected_category='vegetables',
        ),
    )

    assert listing.image_source == 'seller_upload'
    assert str(listing.image_url) == 'http://localhost:8000/media/listings/f8e86bbffaddeb22810dd7c3.jpg'
    assert listing.quality_assessment_source == 'ai_visual'
    assert listing.quality_proof_images == [str(listing.image_url)]
    assert listing.freshness_label == 'AI photo checked'


def test_listing_without_seller_image_uses_catalog_photo_without_ai_visual_claim() -> None:
    store = _test_store('test_listing_catalog_image')
    marketplace = _configure_marketplace(store)

    listing = marketplace.create_listing_from_message(
        seller_id='seller-1',
        seller_name='Shakti FPO',
        message_text='40 kilo onion, 24 rupees kilo, Nashik pickup',
        image_url=None,
    )

    assert listing.image_url
    assert listing.image_source in {'produce_catalog', 'generic_catalog'}
    assert 'data:image/svg+xml' not in str(listing.image_url)
    assert not str(listing.image_url).endswith('.svg')
    assert listing.quality_assessment_source == 'text_signal'
    assert listing.freshness_label != 'AI photo checked'
    assert listing.quality_proof_images == []


def test_unknown_produce_uses_generic_real_produce_photo() -> None:
    store = _test_store('test_listing_generic_image')
    marketplace = _configure_marketplace(store)

    listing = marketplace.create_listing_from_message(
        seller_id='seller-1',
        seller_name='Shakti FPO',
        message_text='12 kilo dragon pods, 60 rupees kilo, Nashik pickup',
        image_url=None,
    )

    assert listing.image_source == 'generic_catalog'
    assert str(listing.image_url) == 'http://localhost:8000/media/default-produce/generic-produce.jpg'


def test_delivery_partner_assignment_persists_and_notifies_both_parties() -> None:
    store = _test_store('test_delivery_partner_assignment')
    listing = _seed_listing(store)
    marketplace = _configure_marketplace(store)

    order = marketplace.place_order(payload=_direct_order_payload(listing.id))
    marketplace.respond_to_order(order.id, 'accept')

    deliveries = marketplace.list_deliveries(buyer_id='9999999999')
    assert len(deliveries) == 1
    delivery = deliveries[0]
    assert delivery.delivery_partner_id is not None
    assert delivery.partner_assigned_by == 'ops-auto-dispatch'
    assert store.get_delivery(delivery.id).delivery_partner_id == delivery.delivery_partner_id  # type: ignore[union-attr]

    notes = store.list_notifications()
    seller_note = next(note for note in notes if note['recipient_role'] == 'seller' and note['entity_id'] == delivery.id and 'partner' in note['title'].lower())
    buyer_note = next(note for note in notes if note['recipient_role'] == 'buyer' and note['entity_id'] == delivery.id and note['category'] == 'delivery')
    assert delivery.delivery_partner_name in seller_note['text']
    assert delivery.delivery_partner_id in seller_note['text']
    assert delivery.delivery_partner_name in buyer_note['text']
    assert delivery.delivery_partner_id in buyer_note['text']


def test_reassigning_partner_is_idempotent_and_releases_previous_partner() -> None:
    store = _test_store('test_delivery_partner_reassign')
    listing = _seed_listing(store)
    marketplace = _configure_marketplace(store)

    order = marketplace.place_order(payload=_direct_order_payload(listing.id))
    marketplace.respond_to_order(order.id, 'accept')
    delivery = marketplace.list_deliveries(buyer_id='9999999999')[0]
    original_partner_id = delivery.delivery_partner_id
    assert original_partner_id is not None

    same_delivery = marketplace.reassign_delivery_partner(delivery.id, original_partner_id, 'ops-demo-1')
    assert same_delivery.delivery_partner_id == original_partner_id

    updated = marketplace.reassign_delivery_partner(delivery.id, 'DP-1002', 'ops-demo-1')
    assert updated.delivery_partner_id == 'DP-1002'
    assert store.get_delivery_partner(original_partner_id).status == 'available'  # type: ignore[union-attr]
    assert store.get_delivery_partner('DP-1002').current_delivery_id == delivery.id  # type: ignore[union-attr]


def test_settled_delivery_releases_partner_and_pool_deliveries_receive_partners() -> None:
    store = _test_store('test_delivery_partner_release_and_pool')
    listing = _seed_listing(store)
    marketplace = _configure_marketplace(store)

    marketplace.create_demand_request(DemandRequestCreate(
        buyer_id='buyer-1',
        buyer_name='Buyer One',
        product_query='tomato',
        quantity_kg=10,
        delivery_mode='delivery',
        delivery_address='Lajpat Nagar, Delhi',
        needed_by='Today',
        phone='9999990001',
    ))
    marketplace.create_demand_request(DemandRequestCreate(
        buyer_id='buyer-2',
        buyer_name='Buyer Two',
        product_query='tomato',
        quantity_kg=12,
        delivery_mode='delivery',
        delivery_address='Lajpat Nagar, Delhi',
        needed_by='Today',
        phone='9999990002',
    ))
    pool = store.list_commit_pools()[0]
    result = marketplace.commit_to_pool(pool.id, type('PoolCommitPayload', (), {
        'seller_id': listing.seller_id,
        'listing_id': listing.id,
        'price_per_kg': listing.price_per_kg,
    })())
    assert result['deliveries']
    assert all(item.delivery_partner_id for item in result['deliveries'])

    order = marketplace.place_order(payload=_direct_order_payload(listing.id, quantity_kg=5.0))
    marketplace.respond_to_order(order.id, 'accept')
    delivery = marketplace.list_deliveries(buyer_id='9999999999')[0]
    partner_id = delivery.delivery_partner_id
    assert partner_id is not None

    marketplace.advance_delivery_for_actor(delivery.id, _advance_payload('quality_check_pending'))
    marketplace.advance_delivery_for_actor(delivery.id, _advance_payload('quality_approved'))
    marketplace.advance_delivery_for_actor(delivery.id, _advance_payload('picked_up'))
    marketplace.advance_delivery_for_actor(delivery.id, _advance_payload('in_transit'))
    marketplace.advance_delivery_for_actor(delivery.id, _advance_payload('delivered'))
    marketplace.advance_delivery_for_actor(delivery.id, _advance_payload('settled'))

    assert store.get_delivery_partner(partner_id).status == 'available'  # type: ignore[union-attr]


def test_legacy_delivery_without_partner_fields_still_deserializes() -> None:
    payload = {
        'id': 'dlv_legacy',
        'order_id': 'ord_legacy',
        'seller_id': 'seller-1',
        'seller_name': 'Seller',
        'buyer_id': 'buyer-1',
        'buyer_name': 'Buyer',
        'product_name': 'Tomato',
        'quantity_kg': 10,
        'delivery_fee': 20,
        'status': 'order_accepted',
        'created_at': '2026-06-13T00:00:00Z',
        'updated_at': '2026-06-13T00:00:00Z',
    }
    delivery = Delivery.model_validate(payload)
    assert delivery.delivery_partner_id is None
    assert delivery.assignment_status is None
