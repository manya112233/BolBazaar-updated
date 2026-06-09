from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / 'backend'
TMP_DIR = BACKEND_DIR / 'tmp'
TMP_DIR.mkdir(parents=True, exist_ok=True)

os.environ.setdefault('APP_ENV', 'development')
os.environ.setdefault('STORAGE_MODE', 'local')
os.environ.setdefault('ALLOW_LOCAL_FALLBACK', 'true')
os.environ['DATA_FILE'] = str(TMP_DIR / 'smoke_demo_db.json')
os.environ['MEDIA_DIR'] = str(TMP_DIR / 'media')

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient

from app.main import app


def assert_step(condition: bool, label: str) -> None:
    if not condition:
        print(f'FAIL: {label}')
        raise SystemExit(1)
    print(f'PASS: {label}')


def main() -> None:
    client = TestClient(app)

    seed = client.post('/api/demo/seed')
    assert_step(seed.status_code == 200, 'seed demo data')

    ops = client.get('/api/ops/dashboard')
    assert_step(ops.status_code == 200, 'fetch ops dashboard')
    ops_payload = ops.json()
    assert_step(bool(ops_payload['pending_quality_checks']), 'ops dashboard includes pending quality listing')

    listings_response = client.get('/api/listings')
    assert_step(listings_response.status_code == 200, 'fetch listings')
    listings = listings_response.json()['items']
    assert_step(any(item['quality_status'] == 'pending' for item in listings), 'whatsapp/demo listing starts pending')
    assert_step(any(item['quality_status'] == 'approved' for item in listings), 'verified listing visible to buyer marketplace')
    assert_step(any(item['quality_status'] == 'rejected' for item in listings), 'rejected listing visible for quality workflow')

    pending_listing = next(item for item in listings if item['quality_status'] == 'pending')
    approve = client.post(
        f"/api/ops/listings/{pending_listing['id']}/quality",
        json={
            'status': 'approved',
            'grade': 'A',
            'notes': 'Smoke test approval',
            'checked_by': 'ops-smoke',
            'confidence': 0.93,
        },
    )
    assert_step(approve.status_code == 200, 'approve pending listing from ops')

    approved_listing = approve.json()['listing']
    order = client.post(
        '/api/orders',
        json={
            'listing_id': approved_listing['id'],
            'buyer_name': 'Smoke Buyer',
            'buyer_type': 'retailer',
            'quantity_kg': 5,
            'pickup_time': 'Today 6 PM',
            'delivery_mode': 'delivery',
            'delivery_address': 'Lajpat Nagar, Delhi',
        },
    )
    assert_step(order.status_code == 200, 'buyer places delivery order')
    order_payload = order.json()['order']

    respond = client.post(f"/api/orders/{order_payload['id']}/respond", json={'decision': 'accept'})
    assert_step(respond.status_code == 200, 'seller accepts order')

    deliveries = client.get(f"/api/deliveries?seller_id={approved_listing['seller_id']}")
    assert_step(deliveries.status_code == 200, 'fetch seller deliveries')
    delivery = next(item for item in deliveries.json()['items'] if item['order_id'] == order_payload['id'])
    assert_step(delivery['status'] in {'order_accepted', 'quality_approved', 'packed'}, 'delivery created after seller acceptance')

    steps = [
        ('/api/ops/deliveries/{id}/advance', {'next_status': 'quality_check_pending', 'actor_role': 'ops', 'actor_id': 'ops-smoke'}, 'ops marks quality_check_pending'),
        ('/api/ops/deliveries/{id}/advance', {'next_status': 'quality_approved', 'actor_role': 'ops', 'actor_id': 'ops-smoke'}, 'ops marks quality_approved'),
        ('/api/ops/deliveries/{id}/advance', {'next_status': 'packed', 'actor_role': 'seller', 'actor_id': approved_listing['seller_id']}, 'seller marks packed'),
        ('/api/ops/deliveries/{id}/advance', {'next_status': 'handover_pending', 'actor_role': 'seller', 'actor_id': approved_listing['seller_id']}, 'seller marks handover'),
        ('/api/ops/deliveries/{id}/advance', {'next_status': 'picked_up', 'actor_role': 'ops', 'actor_id': 'ops-smoke'}, 'ops marks picked_up'),
        ('/api/ops/deliveries/{id}/advance', {'next_status': 'in_transit', 'actor_role': 'ops', 'actor_id': 'ops-smoke'}, 'ops marks in_transit'),
        ('/api/ops/deliveries/{id}/advance', {'next_status': 'delivered', 'actor_role': 'ops', 'actor_id': 'ops-smoke'}, 'ops marks delivered'),
    ]

    for path_template, payload, label in steps:
        response = client.post(path_template.format(id=delivery['id']), json=payload)
        assert_step(response.status_code == 200, label)

    confirm = client.post(
        f"/api/buyers/deliveries/{delivery['id']}/confirm",
        json={'buyer_id': 'smoke-buyer-1', 'quality_issue': False},
    )
    assert_step(confirm.status_code == 200, 'buyer confirms received')
    assert_step(confirm.json()['delivery']['status'] == 'buyer_confirmed', 'final buyer-confirmed status returned')

    metrics = client.get('/api/ops/metrics')
    assert_step(metrics.status_code == 200, 'fetch ops metrics')
    metrics_payload = metrics.json()
    assert_step(metrics_payload['verified_listings'] >= 1, 'verified listing counted in metrics')
    assert_step(metrics_payload['completed_deliveries'] >= 1, 'completed delivery counted in metrics')

    print('PASS: supply-chain smoke test completed')


if __name__ == '__main__':
    main()
