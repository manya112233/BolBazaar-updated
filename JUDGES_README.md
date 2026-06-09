# BolBazaar For Judges

## What BolBazaar Does

BolBazaar is a WhatsApp-first agri-commerce workflow for farmers, FPOs, aggregators, and B2B buyers. It converts seller WhatsApp messages into structured produce listings, adds quality verification and grading, exposes trusted supply to buyers, and manages delivery through seller, ops, and buyer stages.

## Why This Fits Smart Supply Chain

BolBazaar is not only a marketplace. It connects supply creation, quality trust, buyer discovery, delivery execution, and impact metrics in one operational loop:

- seller creates supply on WhatsApp
- ops verifies and grades it
- buyer sees trusted supply
- seller and ops manage fulfillment
- buyer confirms receipt
- metrics show verified supply-chain performance

This reduces friction, improves trust, and makes fragmented produce movement visible and manageable.

## SDGs

- `SDG 2`: Zero Hunger
- `SDG 8`: Decent Work and Economic Growth
- `SDG 9`: Industry, Innovation and Infrastructure
- `SDG 12`: Responsible Consumption and Production

## Google Technologies Used

- `Google Gemini` for listing extraction and produce-quality signal support
- `Google Speech-to-Text` for seller voice note workflows
- `Google Text-to-Speech` for voice response support
- `Google Maps / Geocoding` for pickup and location normalization
- `FastAPI + local JSON fallback / Firestore-ready storage` for a demo-friendly but extensible backend

## Demo Story Supported

Seller WhatsApp listing -> BolBazaar quality verification -> buyer sees verified graded supply -> seller packs/hands over on WhatsApp -> ops manages delivery -> buyer confirms received -> metrics update

## Demo Roles

- `buyer`: verified marketplace, demand, ordering, buyer delivery confirmation
- `seller`: listings, orders, khata, seller-side delivery actions
- `ops`: quality verification, managed delivery, supply-chain metrics

## Run Checklist

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

### Seed Demo Data

```powershell
curl -X POST http://localhost:8000/api/demo/seed
```

### Smoke Test

```powershell
python backend\smoke_test_supply_chain.py
```

### Type Check

```powershell
cd frontend
node node_modules/typescript/bin/tsc -b
```

## WhatsApp Commands To Test

### Seller delivery and status

- `DELIVERIES`
- `STATUS`
- `QUALITY`
- `delivery <id> packed`
- `delivery <id> handover`
- `delivery <id> cancel`

### Seller order actions

- `ORDERS`
- `ACCEPT ORDER <order_id>`
- `REJECT ORDER <order_id>`

### Interactive button IDs

- `delivery_advance:<delivery_id>:packed`
- `delivery_advance:<delivery_id>:handover`
- `delivery_cancel:<delivery_id>`

## Seeded Demo State

`POST /api/demo/seed` creates a judge-friendly scenario with:

- 3 sellers
- 3 buyers in the story
- 1 pending tomato listing
- 1 Grade A verified tomato listing
- 1 Grade B verified onion listing
- 1 rejected listing
- 1 pending order
- 1 seller handover-stage managed delivery
- 1 in-transit managed delivery
- 1 delivered order awaiting buyer confirmation
- non-zero supply-chain metrics

## Known Limitations

- Real WhatsApp send and receive requires valid `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, and `WHATSAPP_VERIFY_TOKEN`.
- Google voice features require Google credentials to fully remove local warning logs.
- On some Windows environments, `npm run build` may fail with `esbuild spawn EPERM`; `node node_modules/typescript/bin/tsc -b` is the reliable local validation command.
- Legacy pytest coverage is still noisier than the standalone demo validation script. Use `python backend\smoke_test_supply_chain.py` as the reliable end-to-end demo check.
