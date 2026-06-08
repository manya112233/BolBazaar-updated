from pathlib import Path
from typing import Any
from fastapi.testclient import TestClient

from app.dependencies import get_marketplace, get_store
from app.main import app
from app.schemas import SellerProfile, Listing, DemandRequestCreate, ListingCreate
from app.services.marketplace import MarketplaceService
from app.services.store import JsonStore


class MockWhatsApp:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []
        self.reply_buttons: list[dict[str, Any]] = []

    def send_text_message(self, to: str, body: str) -> dict[str, Any]:
        self.messages.append({'to': to, 'body': body})
        return {'sent': True, 'message_id': 'mock_msg_id'}

    def send_reply_buttons(self, to: str, body: str, buttons: list[dict[str, str]]) -> dict[str, Any]:
        self.reply_buttons.append({'to': to, 'body': body, 'buttons': buttons})
        return {'sent': True, 'message_id': 'mock_btn_id'}

    def delivery_status(self, result: dict[str, Any]) -> str:
        return 'sent' if result.get('sent') else 'failed'


def _build_test_client(store: JsonStore, marketplace: MarketplaceService) -> TestClient:
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace
    return TestClient(app)


def test_create_demand_request_groups_into_pool(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = MarketplaceService(store)
    client = _build_test_client(store, marketplace)

    try:
        payload = {
            'buyer_id': 'buyer-1',
            'buyer_name': 'Kishan Store',
            'product_query': 'tomato',
            'quantity_kg': 15.0,
            'max_price_per_kg': 35.0,
            'delivery_mode': 'delivery',
            'delivery_address': 'Lajpat Nagar, Delhi',
            'needed_by': 'Today evening',
            'phone': '+919876543210',
        }

        response = client.post('/api/buyers/demand-requests', json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        req_id = data['request']['id']

        # Verify demand request is in store
        req = store.get_demand_request(req_id)
        assert req is not None
        assert req.product_name == 'Tomato'
        assert req.quantity_kg == 15.0

        # Verify pool is automatically created/rebuilt
        pools = store.list_commit_pools()
        assert len(pools) == 1
        pool = pools[0]
        assert pool.product_name == 'Tomato'
        assert pool.total_quantity_kg == 15.0
        assert len(pool.members) == 1
        assert pool.members[0].buyer_id == 'buyer-1'
    finally:
        app.dependency_overrides.clear()


def test_seller_commits_to_pool(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = MarketplaceService(store)
    whatsapp = MockWhatsApp()
    marketplace.whatsapp = whatsapp  # type: ignore[assignment]
    client = _build_test_client(store, marketplace)

    try:
        # Seed seller
        store.save_seller_profile(
            SellerProfile(
                seller_id='seller-1',
                seller_name='Ramesh Kumar',
                store_name='Ramesh Farms',
                preferred_language='en',
                registration_status='active',
                default_pickup_location='South Delhi',
                latitude=28.57,
                longitude=77.24,
            )
        )

        # Seed listing
        listing = marketplace.store.save_listing(
            Listing(
                seller_id='seller-1',
                seller_name='Ramesh Kumar',
                product_name='Tomato',
                category='vegetables',
                quantity_kg=100.0,
                available_kg=100.0,
                price_per_kg=30.0,
                pickup_location='South Delhi',
                latitude=28.57,
                longitude=77.24,
            )
        )

        # Create two buyer demands
        marketplace.create_demand_request(
            DemandRequestCreate(
                buyer_id='buyer-1',
                buyer_name='Kirana A',
                product_query='fresh tomato',
                quantity_kg=20.0,
                max_price_per_kg=35.0,
                delivery_mode='delivery',
                delivery_address='Lajpat Nagar, Delhi',
                needed_by='Today evening',
            )
        )
        marketplace.create_demand_request(
            DemandRequestCreate(
                buyer_id='buyer-2',
                buyer_name='Kirana B',
                product_query='tomato',
                quantity_kg=15.0,
                max_price_per_kg=33.0,
                delivery_mode='delivery',
                delivery_address='Lajpat Nagar, Delhi',
                needed_by='Tomorrow morning',
            )
        )

        pools = store.list_commit_pools()
        assert len(pools) == 1
        pool_id = pools[0].id

        # Commit to pool
        commit_payload = {
            'seller_id': 'seller-1',
            'listing_id': listing.id,
            'price_per_kg': 29.0,
        }
        response = client.post(f'/api/commit-pools/{pool_id}/commit', json=commit_payload)
        assert response.status_code == 200
        res_data = response.json()
        assert res_data['ok'] is True

        # Check listing stock was depleted
        updated_listing = store.get_listing(listing.id)
        assert updated_listing is not None
        assert updated_listing.available_kg == 65.0  # 100 - 20 - 15

        # Check pool status is committed
        updated_pool = store.get_commit_pool(pool_id)
        assert updated_pool is not None
        assert updated_pool.status == 'committed'
        assert updated_pool.committed_seller_id == 'seller-1'

        # Check that orders and deliveries were created
        orders = store.list_orders()
        assert len(orders) == 2
        for order in orders:
            assert order.status == 'accepted'
            assert order.pool_id == pool_id
            assert order.delivery_mode == 'delivery'

        deliveries = store.list_deliveries()
        assert len(deliveries) == 2
        for dlv in deliveries:
            assert dlv.pool_id == pool_id
            assert dlv.seller_id == 'seller-1'
            assert dlv.status == 'accepted'
    finally:
        app.dependency_overrides.clear()


def test_delivery_lifecycle(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = MarketplaceService(store)
    client = _build_test_client(store, marketplace)

    try:
        # Create a delivery directly in the store
        from app.schemas import Delivery
        dlv = Delivery(
            order_id='ord-1',
            seller_id='seller-1',
            seller_name='Ramesh',
            buyer_name='Kirana A',
            product_name='Tomato',
            quantity_kg=20.0,
            delivery_mode='delivery',
            delivery_address='Lajpat Nagar',
            delivery_fee=25.0,
            status='accepted',
        )
        store.save_delivery(dlv)

        # Advance to packed
        response = client.post(f'/api/deliveries/{dlv.id}/advance', json={'status': 'packed'})
        assert response.status_code == 200
        assert response.json()['delivery']['status'] == 'packed'

        # Advance to out_for_delivery
        response = client.post(f'/api/deliveries/{dlv.id}/advance', json={'status': 'out_for_delivery'})
        assert response.status_code == 200
        assert response.json()['delivery']['status'] == 'out_for_delivery'

        # Advance to delivered
        response = client.post(f'/api/deliveries/{dlv.id}/advance', json={'status': 'delivered'})
        assert response.status_code == 200
        assert response.json()['delivery']['status'] == 'delivered'

        # Trying to advance or change status after delivered should fail
        response = client.post(f'/api/deliveries/{dlv.id}/advance', json={'status': 'cancelled'})
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()
