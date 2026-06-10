from __future__ import annotations

from pathlib import Path
from typing import Any

from app.schemas import Listing, NotificationRecord, SellerProfile
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
    )
    store.save_listing(listing)
    return listing


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
    marketplace = MarketplaceService(store)
    marketplace.whatsapp = SilentWhatsApp()  # type: ignore[assignment]
    marketplace.geo.resolve_distance = lambda **_: (10.0, 'haversine')  # type: ignore[method-assign]
    marketplace.geo.geocode = lambda location: {'pickup_location': location, 'latitude': 28.6, 'longitude': 77.2, 'place_id': 'demo'}  # type: ignore[method-assign]

    order = marketplace.place_order(
        payload=type('OrderPayload', (), {
            'listing_id': listing.id,
            'buyer_name': 'Sunrise Kirana',
            'buyer_type': 'kirana',
            'quantity_kg': 20.0,
            'pickup_time': 'Today 5 PM',
            'phone': '9999999999',
            'delivery_mode': 'delivery',
            'delivery_address': 'Lajpat Nagar, Delhi',
        })()
    )

    assert order.delivery_fee == 162
    assert order.delivery_distance_km == 10.0
    assert order.buyer_total_payable == 762
    assert order.delivery_fee_breakdown is not None


def test_direct_delivery_orders_remain_visible_to_buyer_after_acceptance() -> None:
    store = _test_store('test_buyer_delivery_visibility')
    listing = _seed_listing(store)
    marketplace = MarketplaceService(store)
    marketplace.whatsapp = SilentWhatsApp()  # type: ignore[assignment]
    marketplace.geo.resolve_distance = lambda **_: (10.0, 'haversine')  # type: ignore[method-assign]
    marketplace.geo.geocode = lambda location: {'pickup_location': location, 'latitude': 28.6, 'longitude': 77.2, 'place_id': 'demo'}  # type: ignore[method-assign]

    order = marketplace.place_order(
        payload=type('OrderPayload', (), {
            'listing_id': listing.id,
            'buyer_name': 'Sunrise Kirana',
            'buyer_type': 'kirana',
            'quantity_kg': 10.0,
            'pickup_time': 'Today 5 PM',
            'phone': '9999999999',
            'delivery_mode': 'delivery',
            'delivery_address': 'Lajpat Nagar, Delhi',
        })()
    )

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
    assert 'मंडी' in whatsapp.messages[-1]['body']
