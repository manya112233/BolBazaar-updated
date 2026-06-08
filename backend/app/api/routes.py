from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.dependencies import get_auth_service, get_marketplace, get_store
from datetime import datetime

from app.schemas import BuyerDemandSearchIn, BuyerDemandSearchResponse, DemoSeedResponse, LedgerPaymentCreate, ListingResponse, OrderCreate, OrderDecisionIn, OtpRequestIn, OtpRequestResponse, OtpVerifyIn, OtpVerifyResponse, SellerLedgerView, SellerMessageIn, SellerProfile
from app.services.auth_service import AuthService
from app.services.marketplace import MarketplaceService
from app.services.seller_flow import SellerFlowService
from app.services.speech_service import SpeechService
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@router.post('/demo/seed', response_model=DemoSeedResponse)
def seed_demo(store: Any = Depends(get_store)) -> DemoSeedResponse:
    store.reset()
    return DemoSeedResponse(ok=True, message='Demo store reset successfully')


@router.post('/demo/seller-message')
def demo_seller_message(
    payload: SellerMessageIn,
    marketplace: MarketplaceService = Depends(get_marketplace),
    store: Any = Depends(get_store),
) -> dict:
    effective_message = payload.transcript_text or payload.message_text
    if not effective_message:
        raise HTTPException(status_code=400, detail='message_text or transcript_text is required')

    listing = marketplace.create_listing_from_message(
        seller_id=payload.seller_id,
        seller_name=payload.seller_name,
        message_text=effective_message,
        image_url=str(payload.image_url) if payload.image_url else None,
        source_channel=payload.source_channel,
    )
    existing_profile = store.get_seller_profile(payload.seller_id)
    if existing_profile is None:
        store.save_seller_profile(
            SellerProfile(
                seller_id=payload.seller_id,
                seller_name=payload.seller_name,
                store_name=payload.seller_name,
                preferred_language='hi',
                default_pickup_location=listing.pickup_location,
                latitude=listing.latitude,
                longitude=listing.longitude,
                place_id=listing.place_id,
                registration_status='active',
                source_channel=payload.source_channel,
                updated_at=datetime.utcnow(),
            )
        )
    return {
        'ok': True,
        'seller_message': effective_message,
        'confirmation_text': f'Listing live: {listing.product_name}, {listing.available_kg} kg at {listing.price_per_kg}/kg.',
        'listing': listing,
    }


@router.post('/auth/otp/request', response_model=OtpRequestResponse)
def request_login_otp(
    payload: OtpRequestIn,
    auth_service: AuthService = Depends(get_auth_service),
) -> OtpRequestResponse:
    try:
        return auth_service.request_otp(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/auth/otp/verify', response_model=OtpVerifyResponse)
def verify_login_otp(
    payload: OtpVerifyIn,
    auth_service: AuthService = Depends(get_auth_service),
) -> OtpVerifyResponse:
    try:
        return auth_service.verify_otp(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/listings', response_model=ListingResponse)
def list_listings(marketplace: MarketplaceService = Depends(get_marketplace)) -> ListingResponse:
    return ListingResponse(items=marketplace.list_live_listings())


@router.post('/buyers/demand-search', response_model=BuyerDemandSearchResponse)
def record_buyer_demand_search(
    payload: BuyerDemandSearchIn,
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> BuyerDemandSearchResponse:
    return marketplace.process_buyer_demand_search(payload)


@router.get('/listings/{listing_id}')
def get_listing(listing_id: str, store: Any = Depends(get_store)) -> dict:
    listing = store.get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail='Listing not found')
    return listing.model_dump()


@router.post('/orders')
def create_order(payload: OrderCreate, marketplace: MarketplaceService = Depends(get_marketplace)) -> dict:
    try:
        order = marketplace.place_order(payload)
        return {'ok': True, 'order': order}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/orders/{order_id}/respond')
def respond_to_order(order_id: str, payload: OrderDecisionIn, marketplace: MarketplaceService = Depends(get_marketplace)) -> dict:
    try:
        order = marketplace.respond_to_order(order_id=order_id, decision=payload.decision)
        return {'ok': True, 'order': order}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/orders')
def list_orders(store: Any = Depends(get_store)) -> dict:
    get_listing = getattr(store, 'get_listing', None)
    orders = []
    for order in store.list_orders():
        if get_listing is not None and (not order.product_name or order.product_name == 'items'):
            listing = get_listing(order.listing_id)
            if listing is not None:
                order.product_name = listing.product_name
        orders.append(order)
    return {'items': orders}


@router.get('/notifications')
def list_notifications(store: Any = Depends(get_store)) -> dict:
    return {'items': store.list_notifications()}


@router.get('/sellers')
def list_sellers(marketplace: MarketplaceService = Depends(get_marketplace)) -> dict:
    return {'items': [item.model_dump() for item in marketplace.list_seller_profiles()]}


@router.get('/sellers/{seller_id}/dashboard')
def get_seller_dashboard(seller_id: str, marketplace: MarketplaceService = Depends(get_marketplace)) -> dict:
    dashboard = marketplace.build_seller_dashboard(seller_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail='Seller dashboard not found')
    return dashboard.model_dump()


@router.get('/sellers/{seller_id}/ledger', response_model=SellerLedgerView)
def get_seller_ledger(seller_id: str, marketplace: MarketplaceService = Depends(get_marketplace)) -> SellerLedgerView:
    ledger = marketplace.build_seller_ledger(seller_id)
    if ledger is None:
        raise HTTPException(status_code=404, detail='Seller ledger not found')
    return ledger


@router.post('/sellers/{seller_id}/ledger/payments')
def create_seller_ledger_payment(
    seller_id: str,
    payload: LedgerPaymentCreate,
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    try:
        entry = marketplace.record_ledger_payment(seller_id=seller_id, payload=payload)
        ledger = marketplace.build_seller_ledger(seller_id)
        return {'ok': True, 'entry': entry, 'ledger': ledger}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/sellers/{seller_id}/insight')
def get_seller_insight(seller_id: str, store: Any = Depends(get_store)) -> dict:
    insight = store.get_insight(seller_id)
    if insight is None:
        raise HTTPException(status_code=404, detail='No insight available yet')
    return insight.model_dump()


@router.get('/webhooks/whatsapp/inbound', response_class=PlainTextResponse)
def whatsapp_verify(
    hub_mode: str | None = Query(default=None, alias='hub.mode'),
    hub_verify_token: str | None = Query(default=None, alias='hub.verify_token'),
    hub_challenge: str | None = Query(default=None, alias='hub.challenge'),
) -> str:
    service = WhatsAppService()
    try:
        return service.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post('/webhooks/whatsapp/inbound')
async def whatsapp_inbound(
    request: Request,
    marketplace: MarketplaceService = Depends(get_marketplace),
    store: Any = Depends(get_store),
) -> dict:
    payload = await request.json()
    whatsapp = WhatsAppService()
    speech = SpeechService()
    if not whatsapp.is_configured():
        logger.warning(
            'Received inbound WhatsApp message while outbound replies are not configured. Missing: %s',
            ', '.join(whatsapp.missing_outbound_config()),
        )

    parsed = whatsapp.extract_incoming_message(payload)
    if not parsed:
        return {'ok': True, 'ignored': True}

    value = parsed['value']
    message = parsed['message']
    message_id = str(message.get('id') or '')

    if message_id and not store.claim_whatsapp_message(message_id):
        logger.info('Ignoring duplicate WhatsApp message id: %s', message_id)
        return {'ok': True, 'ignored': True, 'reason': 'duplicate_message'}

    profile_name = parsed.get('profile_name') or 'WhatsApp Seller'
    seller_id = str(message.get('from') or 'seller-whatsapp')
    image_url = None
    image_bytes = None
    image_mime_type = None
    message_text = ''
    interaction_id = None
    had_audio = False
    capture_mode = 'text_message'

    try:
        for item in value.get('messages', []):
            msg_type = item.get('type')
            if msg_type == 'text':
                message_text = f"{message_text} {item.get('text', {}).get('body', '')}".strip()
            elif msg_type == 'image':
                media_id = item.get('image', {}).get('id')
                image_url = image_url or media_id
                caption = item.get('image', {}).get('caption') or ''
                message_text = f'{message_text} {caption}'.strip()
                if media_id and image_bytes is None:
                    image_bytes, image_mime_type = whatsapp.fetch_media_bytes(media_id)
            elif msg_type == 'document':
                image_url = image_url or item.get('document', {}).get('id')
                caption = item.get('document', {}).get('caption') or ''
                message_text = f'{message_text} {caption}'.strip()
            elif msg_type == 'interactive':
                interactive = item.get('interactive', {})
                reply_type = interactive.get('type')
                reply = interactive.get(reply_type, {}) if reply_type else {}
                interaction_id = str(reply.get('id') or '').strip() or None
                if not message_text:
                    message_text = str(reply.get('title') or '').strip()
            elif msg_type == 'audio':
                had_audio = True
                capture_mode = 'voice_note'
                media_id = item.get('audio', {}).get('id')
                if media_id:
                    audio_bytes, mime_type = whatsapp.fetch_media_bytes(media_id)
                    transcript = speech.transcribe_bytes(audio_bytes or b'', mime_type or 'audio/ogg') if audio_bytes else None
                    if transcript:
                        message_text = f'{message_text} {transcript}'.strip()
                    else:
                        logger.info('No transcript generated for WhatsApp audio message %s', message_id or '<no-id>')
    except Exception:
        if message_id:
            store.release_whatsapp_message_claim(message_id)
        raise

    if not message_text and not interaction_id and not image_url:
        logger.info('Ignoring WhatsApp message %s because no text or transcript was extracted', message_id or '<no-id>')
        if had_audio:
            profile = store.get_seller_profile(seller_id)
            if profile is not None and profile.preferred_language == 'hi':
                fallback_text = 'वॉइस मैसेज अभी प्रोसेस नहीं हो पाया। कृपया टेक्स्ट में product, kilo, price और pickup भेजें।'
            else:
                fallback_text = 'Voice message could not be processed. Please send product, kilo, price, and pickup in text.'
            try:
                whatsapp.send_text_message(to=seller_id, body=fallback_text)
                logger.info('Sent audio fallback reply for WhatsApp message %s', message_id or '<no-id>')
            except Exception as exc:
                logger.warning('Failed to send audio fallback reply for WhatsApp message %s: %s', message_id or '<no-id>', exc)
            if message_id:
                store.mark_whatsapp_message_processed(message_id)
                return {'ok': True, 'ignored': True, 'reason': 'no_transcript_fallback_sent'}
        if message_id:
            store.release_whatsapp_message_claim(message_id)
        return {'ok': True, 'ignored': True, 'reason': 'no_text_or_transcript'}

    seller_flow = SellerFlowService(store=store, marketplace=marketplace, whatsapp=whatsapp)
    try:
        result = seller_flow.handle_message(
            seller_id=seller_id,
            message_text=message_text,
            profile_name=profile_name,
            image_url=image_url,
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            interaction_id=interaction_id,
            capture_mode=capture_mode,
        )
    except Exception:
        if message_id:
            store.release_whatsapp_message_claim(message_id)
        raise

    if message_id:
        store.mark_whatsapp_message_processed(message_id)

    logger.info('Handled WhatsApp message %s for seller %s', message_id or '<no-id>', seller_id)
    return result
