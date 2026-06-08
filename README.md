# BolBazaar

BolBazaar is a WhatsApp-first AI agri-commerce operating system for farmers, FPOs, aggregators, traders, and B2B buyers.

It turns informal seller messages into structured produce listings, buyer orders, khata records, demand signals, and seller insights without forcing sellers to install a new app.

## What It Does

- Sellers create listings through WhatsApp text, voice notes, and images.
- The backend extracts product, quantity, price, and pickup details.
- Buyers browse live listings in a web dashboard and place orders.
- Sellers receive WhatsApp order prompts and can accept or reject orders.
- Khata balances, payments, notifications, and seller insights stay synced.
- Buyer search activity can trigger demand alerts to relevant sellers.

## Stack

### Frontend

- React 18
- TypeScript
- Vite

### Backend

- FastAPI
- Pydantic
- Firestore or local JSON storage fallback
- Google Gemini
- Google Speech-to-Text
- Google Text-to-Speech
- Google Maps Geocoding
- Meta WhatsApp Cloud API

## Product Flows

### Seller Flow

1. Seller sends a text, voice note, or image on WhatsApp.
2. BolBazaar extracts listing data and normalizes pickup/location details.
3. Seller reviews the listing and makes it live.
4. Buyer places an order from the web dashboard.
5. Seller accepts or rejects the order from WhatsApp or the dashboard.
6. Stock, notifications, khata, and insights update in one system.

### Buyer Flow

1. Buyer logs in with OTP on the web app.
2. Buyer searches live listings and trusted sellers.
3. Buyer places an order.
4. Demand searches can be reported to trigger seller alerts.

## Repository Structure

```text
backend/
  app/
    api/
    services/
  data/
  tests/

frontend/
  src/
    components/
    components/dashboard/
    components/landing/
```

## Key Features

- WhatsApp-first seller onboarding
- Hindi and English workflow support
- Voice-note transcription support
- AI listing extraction
- AI produce photo quality assessment
- Seller verification and profile workflow
- Buyer marketplace dashboard
- Seller operations dashboard
- Khata ledger and payment recording
- Demand signal reporting
- Seller insight generation

## Local Development

### 1. Clone

```powershell
git clone https://github.com/manya112233/BolBazaar-updated.git
cd BolBazaar-updated
```

### 2. Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create `backend/.env` from `backend/.env.example`.

Start the backend:

```powershell
$env:PYTHONPATH='.'
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run at:

`http://localhost:8000`

### 3. Frontend Setup

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Create `frontend/.env` from `frontend/.env.example`.

Frontend will run at:

`http://localhost:5173`

## Environment Variables

### Backend

Important keys from `backend/.env.example`:

- `FRONTEND_ORIGIN`
- `STORAGE_MODE`
- `ALLOW_LOCAL_FALLBACK`
- `DATA_FILE`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `GCP_PROJECT_ID`
- `FIREBASE_PROJECT_ID`
- `MAPS_API_KEY`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_VERIFY_TOKEN`

### Frontend

- `VITE_API_BASE_URL=http://localhost:8000`

## Running Without Full Cloud Setup

You can still run the product locally with reduced capability.

- Use `ALLOW_LOCAL_FALLBACK=true`
- Keep a valid `DATA_FILE` path
- If Firestore is unavailable, the app can fall back to local JSON storage

Without full external setup, these features may be limited:

- live WhatsApp messaging
- speech transcription quality
- Gemini extraction and insights
- geocoding normalization

## WhatsApp and Google Setup

To use the full seller flow, configure:

- Meta WhatsApp Cloud API credentials
- Google service account JSON
- Speech-to-Text API
- Firestore
- Gemini API
- Maps Geocoding

Set:

`GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json`

Do not commit your `.env` files or service-account JSON.

## Demo and Testing

### Reset Demo Data

The backend exposes:

- `POST /api/demo/seed`

This resets the demo store.

### Useful API Routes

- `GET /api/health`
- `GET /api/listings`
- `POST /api/orders`
- `POST /api/orders/{order_id}/respond`
- `GET /api/orders`
- `GET /api/notifications`
- `GET /api/sellers`
- `GET /api/sellers/{seller_id}/dashboard`
- `GET /api/sellers/{seller_id}/ledger`
- `POST /api/sellers/{seller_id}/ledger/payments`
- `GET /api/sellers/{seller_id}/insight`
- `POST /api/buyers/demand-search`
- `GET /api/webhooks/whatsapp/inbound`
- `POST /api/webhooks/whatsapp/inbound`

## UI Overview

### Pre-login

- premium scrollable landing page
- product story for judges and demos
- WhatsApp commerce demo
- architecture and comparison sections

### Authenticated

- seller dashboard with sidebar, KPI cards, listings, orders, khata, insights, and verification
- buyer dashboard with marketplace, orders, sellers, and demand signals

## Notes

- This repo uses `.gitignore` to exclude local `.env` files, local virtualenvs, build outputs, logs, and service-account keys.
- Some existing demo media files in `backend/data/media/listings/` are intentionally tracked for sample listings.

## Recommended Demo Script

1. Open the landing page.
2. Show the WhatsApp-first seller story.
3. Log in as seller and show operations, listings, and khata.
4. Log in as buyer and place an order.
5. Show seller order response.
6. Show demand signals and AI insights.

## License

No license file is currently included in this repository.
