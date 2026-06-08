from pathlib import Path

from fastapi.testclient import TestClient

from app.dependencies import get_marketplace, get_store
from app.main import app
from app.schemas import BuyerDemandSearchIn
from app.services.marketplace import MarketplaceService
from app.services.store import JsonStore


def _build_test_client(store: JsonStore, marketplace: MarketplaceService) -> TestClient:
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_marketplace] = lambda: marketplace
    return TestClient(app)


def test_buyer_demand_event_stores_quantity_and_delivery_metadata(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = MarketplaceService(store)
    client = _build_test_client(store, marketplace)

    try:
        response = client.post(
            '/api/buyers/demand-search',
            json={
                'buyer_id': 'buyer-1',
                'search_query': 'tomato',
                'max_price_per_kg': 29,
                'quantity_kg': 25,
                'delivery_location': 'South Delhi',
                'needed_by': 'Tonight',
                'buyer_type': 'restaurant',
            },
        )

        assert response.status_code == 200
        event = store.list_buyer_search_events()[0]
        assert event.detected_product_name == 'Tomato'
        assert event.quantity_kg == 25
        assert event.delivery_location == 'South Delhi'
        assert event.needed_by == 'Tonight'
        assert event.buyer_type == 'restaurant'
    finally:
        app.dependency_overrides.clear()


def test_build_demand_pools_groups_events_and_uses_default_quantity_estimate(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = MarketplaceService(store)

    marketplace.process_buyer_demand_search(
        BuyerDemandSearchIn(
            buyer_id='buyer-1',
            search_query='tomato',
            max_price_per_kg=28,
            quantity_kg=20,
            delivery_location='South Delhi',
            needed_by='Today',
            buyer_type='kirana',
        )
    )
    marketplace.process_buyer_demand_search(
        BuyerDemandSearchIn(
            buyer_id='buyer-2',
            search_query='tomato',
            max_price_per_kg=30,
            delivery_location='Lajpat Nagar',
            needed_by='Tomorrow morning',
            buyer_type='retailer',
        )
    )

    pools = marketplace.build_demand_pools()

    assert len(pools) == 1
    pool = pools[0]
    assert pool.product_name == 'Tomato'
    assert pool.unique_buyer_count == 2
    assert pool.total_quantity_kg == 30
    assert pool.average_max_price_per_kg == 29
    assert pool.min_max_price_per_kg == 28
    assert pool.max_max_price_per_kg == 30
    assert set(pool.delivery_locations) == {'South Delhi', 'Lajpat Nagar'}
    assert set(pool.needed_by_labels) == {'Today', 'Tomorrow morning'}
    assert set(pool.buyer_types) == {'kirana', 'retailer'}
    assert pool.urgency_label == 'Emerging demand'
    assert 'Create a matching Tomato listing' in pool.suggested_action


def test_build_demand_pools_sorts_by_unique_buyers_then_quantity(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = MarketplaceService(store)

    for buyer_id in ['buyer-1', 'buyer-2', 'buyer-3']:
        marketplace.process_buyer_demand_search(
            BuyerDemandSearchIn(
                buyer_id=buyer_id,
                search_query='onion',
                max_price_per_kg=36,
            )
        )

    for buyer_id, quantity in [('buyer-4', 20), ('buyer-5', 25)]:
        marketplace.process_buyer_demand_search(
            BuyerDemandSearchIn(
                buyer_id=buyer_id,
                search_query='potato',
                max_price_per_kg=24,
                quantity_kg=quantity,
            )
        )

    for buyer_id, quantity in [('buyer-6', 10), ('buyer-7', 12)]:
        marketplace.process_buyer_demand_search(
            BuyerDemandSearchIn(
                buyer_id=buyer_id,
                search_query='tomato',
                max_price_per_kg=30,
                quantity_kg=quantity,
            )
        )

    pools = marketplace.build_demand_pools()

    assert [pool.product_name for pool in pools[:3]] == ['Onion', 'Potato', 'Tomato']
    assert pools[0].total_quantity_kg == 30
    assert pools[0].urgency_label == 'High demand'


def test_demand_pools_route_returns_aggregated_items(tmp_path: Path) -> None:
    store = JsonStore(tmp_path / 'db.json')
    marketplace = MarketplaceService(store)
    client = _build_test_client(store, marketplace)

    try:
        marketplace.process_buyer_demand_search(
            BuyerDemandSearchIn(
                buyer_id='buyer-1',
                search_query='tomato',
                quantity_kg=18,
                max_price_per_kg=27,
            )
        )
        marketplace.process_buyer_demand_search(
            BuyerDemandSearchIn(
                buyer_id='buyer-2',
                search_query='tomato',
                quantity_kg=12,
                max_price_per_kg=29,
            )
        )

        response = client.get('/api/demand-pools')
        assert response.status_code == 200
        payload = response.json()
        assert len(payload['items']) == 1
        assert payload['items'][0]['product_name'] == 'Tomato'
        assert payload['items'][0]['total_quantity_kg'] == 30
    finally:
        app.dependency_overrides.clear()
