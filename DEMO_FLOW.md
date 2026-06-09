# BolBazaar Demo Flow

## 2-Minute Solution Challenge Story

1. Seller sends produce on WhatsApp.
   Example: `50 kilo tamatar hai, 28 rupay kilo, Nashik pickup.`

2. BolBazaar creates a listing with `quality_status = pending`.
   If an image is attached, AI quality signals can be suggested before ops review.

3. Ops opens the BolBazaar Ops workspace.
   Review the pending lot, approve it, and assign Grade A, B, or C.

4. Buyer opens the marketplace.
   Show the `BolBazaar Verified` badge, grade, quality note, and verified-only filtering.

5. Buyer places a delivery order.
   Seller accepts the order from web or WhatsApp.

6. Seller manages fulfillment from WhatsApp.
   Use:
   - `DELIVERIES`
   - `delivery <id> packed`
   - `delivery <id> handover`
   - `delivery <id> cancel`

7. Ops advances the managed delivery.
   Move through:
   - `quality_check_pending`
   - `quality_approved`
   - `picked_up`
   - `in_transit`
   - `delivered`

8. Buyer confirms received.
   The delivery moves to `buyer_confirmed`.

9. Show Smart Supply Chain impact.
   Highlight:
   - verified listings
   - pending quality checks
   - active deliveries
   - completed deliveries
   - demand pools matched
   - estimated supply matched

## Demo Login Roles

- `buyer`: marketplace, orders, demand requests, buyer delivery confirmation
- `seller`: listings, khata, orders, seller delivery actions
- `ops`: quality verification, managed delivery, smart supply-chain metrics

## Fast Demo Commands

### Reset demo

```powershell
curl -X POST http://localhost:8000/api/demo/seed
```

### Seller WhatsApp delivery commands

- `DELIVERIES`
- `STATUS`
- `delivery <id> packed`
- `delivery <id> handover`
- `delivery <id> cancel`

### Reliable smoke test

```powershell
python backend\smoke_test_supply_chain.py
```
