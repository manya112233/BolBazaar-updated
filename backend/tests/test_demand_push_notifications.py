from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.dependencies import get_marketplace, get_store
from app.main import app
from app.schemas import SellerProfile
from app.services.marketplace import MarketplaceService
from app.services.store import JsonStore


class RecordingDemandWhatsApp:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def send_text_message(self, to: str, body: str) -> dict[str, Any]:
        self.messages.append({'to': to, 'body': body})
        return {'sent': True}

    def delivery_status(self, result: dict[str, Any]) -> str:
        return 'sent' if result.get('sent') else 'failed'


def _seed_seller(
    store: JsonStore,
    *,
    seller_id: str,
    seller_name: str,
    preferred_language: str = 'en',
    registration_status: str = 'active',
) -> None:
    store.save_seller_profile(
        SellerProfile(
            seller_id=seller_id,
            seller_name=seller_name,
            store_name=f'{seller_name} Store',
            preferred_language=preferred_language,  # type: ignore[arg-type]
            registration_status=registration_status,  # type: ignore[arg-type]
            default_pickup_location='Shanti Nagar',
        )
    )


def _build_test_client(store: JsonStore, marketplace: MarketplaceService) -> TestClient:
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace
    return TestClient(app)


def test_demand_push_below_threshold_records_but_does_not_notify(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    _seed_seller(store, seller_id='919971497076', seller_name='Ramesh')

    marketplace = MarketplaceService(store)
    whatsapp = RecordingDemandWhatsApp()
    marketplace.whatsapp = whatsapp  # type: ignore[assignment]

    client = _build_test_client(store, marketplace)
    try:
        response = client.post(
            '/api/buyers/demand-search',
            json={
                'buyer_id': 'buyer-1',
                'search_query': 'onion needed urgently',
                'max_price_per_kg': 35,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload['threshold_reached'] is False
        assert payload['unique_buyer_count'] == 1
        assert payload['notified_seller_count'] == 0
        assert payload['reason'] == 'below_threshold'
        assert whatsapp.messages == []

        events = store.list_buyer_search_events()
        assert len(events) == 1
        assert events[0].detected_product_name == 'Onion'
    finally:
        app.dependency_overrides.clear()


def test_demand_push_notifies_active_sellers_at_threshold(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    _seed_seller(store, seller_id='919971497076', seller_name='Ramesh', preferred_language='en', registration_status='active')
    _seed_seller(store, seller_id='919971497077', seller_name='Sita', preferred_language='hi', registration_status='active')
    _seed_seller(store, seller_id='919971497078', seller_name='Pending Seller', preferred_language='en', registration_status='pending')

    marketplace = MarketplaceService(store)
    whatsapp = RecordingDemandWhatsApp()
    marketplace.whatsapp = whatsapp  # type: ignore[assignment]

    client = _build_test_client(store, marketplace)
    try:
        for index in range(1, 4):
            response = client.post(
                '/api/buyers/demand-search',
                json={
                    'buyer_id': f'buyer-{index}',
                    'search_query': 'onion',
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload['threshold_reached'] is True
        assert payload['unique_buyer_count'] == 3
        assert payload['notified_seller_count'] == 2

        recipients = {message['to'] for message in whatsapp.messages}
        assert recipients == {'919971497076', '919971497077'}
        assert all('Onion' in message['body'] for message in whatsapp.messages)
        assert any('खरीदार' in message['body'] for message in whatsapp.messages)

        notifications = store.list_notifications()
        assert len(notifications) == 2
    finally:
        app.dependency_overrides.clear()


def test_demand_push_counts_unique_buyers_only(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    _seed_seller(store, seller_id='919971497076', seller_name='Ramesh')

    marketplace = MarketplaceService(store)
    whatsapp = RecordingDemandWhatsApp()
    marketplace.whatsapp = whatsapp  # type: ignore[assignment]

    client = _build_test_client(store, marketplace)
    try:
        first = client.post(
            '/api/buyers/demand-search',
            json={'buyer_id': 'buyer-1', 'search_query': 'tomato'},
        )
        second = client.post(
            '/api/buyers/demand-search',
            json={'buyer_id': 'buyer-1', 'search_query': 'tomato'},
        )
        third = client.post(
            '/api/buyers/demand-search',
            json={'buyer_id': 'buyer-2', 'search_query': 'tomato'},
        )

        assert first.status_code == 200
        assert second.status_code == 200
        assert third.status_code == 200
        assert third.json()['unique_buyer_count'] == 2
        assert third.json()['threshold_reached'] is False

        fourth = client.post(
            '/api/buyers/demand-search',
            json={'buyer_id': 'buyer-3', 'search_query': 'tomato'},
        )

        assert fourth.status_code == 200
        assert fourth.json()['unique_buyer_count'] == 3
        assert fourth.json()['threshold_reached'] is True
        assert fourth.json()['notified_seller_count'] == 1
    finally:
        app.dependency_overrides.clear()


def test_demand_push_cooldown_prevents_repeat_notifications(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    _seed_seller(store, seller_id='919971497076', seller_name='Ramesh')

    marketplace = MarketplaceService(store)
    whatsapp = RecordingDemandWhatsApp()
    marketplace.whatsapp = whatsapp  # type: ignore[assignment]

    client = _build_test_client(store, marketplace)
    try:
        for index in range(1, 4):
            response = client.post(
                '/api/buyers/demand-search',
                json={
                    'buyer_id': f'buyer-{index}',
                    'search_query': 'onion',
                },
            )

        assert response.status_code == 200
        assert response.json()['notified_seller_count'] == 1
        assert len(whatsapp.messages) == 1

        follow_up = client.post(
            '/api/buyers/demand-search',
            json={
                'buyer_id': 'buyer-4',
                'search_query': 'onion',
            },
        )

        assert follow_up.status_code == 200
        assert follow_up.json()['threshold_reached'] is True
        assert follow_up.json()['notified_seller_count'] == 0
        assert follow_up.json()['reason'] == 'cooldown_active_or_delivery_failed'
        assert len(whatsapp.messages) == 1
        assert len(store.list_notifications()) == 1
    finally:
        app.dependency_overrides.clear()


def test_demand_push_ignores_unmapped_queries(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    _seed_seller(store, seller_id='919971497076', seller_name='Ramesh')

    marketplace = MarketplaceService(store)
    whatsapp = RecordingDemandWhatsApp()
    marketplace.whatsapp = whatsapp  # type: ignore[assignment]

    client = _build_test_client(store, marketplace)
    try:
        response = client.post(
            '/api/buyers/demand-search',
            json={
                'buyer_id': 'buyer-1',
                'search_query': 'fresh produce deals near me',
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload['threshold_reached'] is False
        assert payload['unique_buyer_count'] == 0
        assert payload['notified_seller_count'] == 0
        assert payload['reason'] == 'unsupported_query'
        assert whatsapp.messages == []

        events = store.list_buyer_search_events()
        assert len(events) == 1
        assert events[0].detected_product_name is None
    finally:
        app.dependency_overrides.clear()
