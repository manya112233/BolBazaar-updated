from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.dependencies import get_auth_service, get_marketplace, get_store
from datetime import datetime, timedelta

from app.schemas import BuyerDemandEvent, BuyerDemandSearchIn, BuyerDemandSearchResponse, BuyerDeliveryConfirmIn, DeliveryAdvanceIn, DeliveryAdvanceRequestIn, DeliveryEstimateIn, DeliveryEstimateResponse, DeliveryPartnerAssignIn, DemandPoolResponse, DemoSeedResponse, LedgerPaymentCreate, ListingQualityUpdateIn, ListingResponse, NotificationReadAllIn, OrderCreate, OrderDecisionIn, OtpRequestIn, OtpRequestResponse, OtpVerifyIn, OtpVerifyResponse, PricingSuggestionIn, SellerLedgerView, SellerMessageIn, SellerProfile, DemandRequestCreate, PoolCommitIn
from app.services.auth_service import AuthService
from app.services.marketplace import MarketplaceService
from app.services.seller_flow import SellerFlowService
from app.services.speech_service import SpeechService
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()
logger = logging.getLogger(__name__)


def _seed_demo_demand_pools(store: Any) -> None:
    save_event = getattr(store, 'save_buyer_search_event', None)
    if not callable(save_event):
        return

    base_time = datetime.utcnow()
    seeded_events = [
        BuyerDemandEvent(
            buyer_id='demo-buyer-1',
            search_query='tomato for kirana',
            normalized_query='tomato for kirana',
            detected_product_name='Tomato',
            detected_category='vegetables',
            max_price_per_kg=28,
            quantity_kg=20,
            delivery_location='South Delhi',
            needed_by='Today evening',
            buyer_type='kirana',
            created_at=base_time - timedelta(minutes=18),
        ),
        BuyerDemandEvent(
            buyer_id='demo-buyer-2',
            search_query='tomato for restaurant',
            normalized_query='tomato for restaurant',
            detected_product_name='Tomato',
            detected_category='vegetables',
            max_price_per_kg=30,
            quantity_kg=15,
            delivery_location='South Delhi',
            needed_by='Tomorrow morning',
            buyer_type='restaurant',
            created_at=base_time - timedelta(minutes=12),
        ),
        BuyerDemandEvent(
            buyer_id='demo-buyer-3',
            search_query='fresh tomato',
            normalized_query='fresh tomato',
            detected_product_name='Tomato',
            detected_category='vegetables',
            max_price_per_kg=29,
            delivery_location='Lajpat Nagar',
            needed_by='Today',
            buyer_type='retailer',
            created_at=base_time - timedelta(minutes=7),
        ),
    ]
    for event in seeded_events:
        save_event(event)


def _seed_demo_supply_chain(store: Any, marketplace: MarketplaceService) -> None:
    now = datetime.utcnow()
    sellers = [
        SellerProfile(
            seller_id='919971497076',
            seller_name='Shakti FPO',
            store_name='Shakti FPO Tomatoes',
            preferred_language='hi',
            default_pickup_location='Nashik Collection Hub',
            registration_status='active',
            verification_status='verified',
            seller_type='fpo',
            source_channel='whatsapp',
            updated_at=now,
        ),
        SellerProfile(
            seller_id='918111111111',
            seller_name='Kisan Fresh',
            store_name='Kisan Fresh Produce',
            preferred_language='en',
            default_pickup_location='Pune Market Yard',
            registration_status='active',
            verification_status='verified',
            seller_type='farmer',
            source_channel='demo',
            updated_at=now,
        ),
        SellerProfile(
            seller_id='917222222222',
            seller_name='GreenRoute Farms',
            store_name='GreenRoute Farms Bengaluru',
            preferred_language='en',
            default_pickup_location='Yeshwanthpur Aggregation Point',
            registration_status='active',
            verification_status='verified',
            seller_type='aggregator',
            source_channel='demo',
            updated_at=now,
        ),
    ]
    for profile in sellers:
        store.save_seller_profile(profile)

    pending_tomato_listing = marketplace.create_listing_from_message(
        seller_id='919971497076',
        seller_name='Shakti FPO',
        message_text='72 kilo tomato, 27 rupees kilo, Nashik Collection Hub pickup',
        image_url='https://images.unsplash.com/photo-1546470427-e6ac89a99c4d?auto=format&fit=crop&w=1200&q=80',
        source_channel='whatsapp',
    )
    verified_tomato_listing = marketplace.create_listing_from_message(
        seller_id='919971497076',
        seller_name='Shakti FPO',
        message_text='48 kilo premium tomato, 31 rupees kilo, Nashik Collection Hub pickup',
        image_url='https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=1200&q=80',
        source_channel='demo',
    )
    verified_onion_listing = marketplace.create_listing_from_message(
        seller_id='918111111111',
        seller_name='Kisan Fresh',
        message_text='65 kilo onion, 24 rupees kilo, Pune Market Yard pickup',
        image_url='https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=1200&q=80',
        source_channel='demo',
    )
    rejected_listing = marketplace.create_listing_from_message(
        seller_id='917222222222',
        seller_name='GreenRoute Farms',
        message_text='34 kilo spinach, 18 rupees kilo, Yeshwanthpur Aggregation Point pickup',
        image_url='https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=1200&q=80',
        source_channel='demo',
    )

    marketplace.update_listing_quality(
        verified_tomato_listing.id,
        ListingQualityUpdateIn(
            status='approved',
            grade='A',
            notes='BolBazaar Verified: bright red tomato lot, uniform size, and clean crate packing.',
            checked_by='ops-demo-1',
            confidence=0.95,
        ),
    )
    marketplace.update_listing_quality(
        verified_onion_listing.id,
        ListingQualityUpdateIn(
            status='approved',
            grade='B',
            notes='BolBazaar Verified: trade-ready onions with minor size variation but healthy outer skin.',
            checked_by='ops-demo-1',
            confidence=0.86,
        ),
    )
    marketplace.update_listing_quality(
        rejected_listing.id,
        ListingQualityUpdateIn(
            status='rejected',
            notes='Rejected after ops review due to wilted leaves and visible moisture damage.',
            checked_by='ops-demo-1',
            confidence=0.78,
        ),
    )

    marketplace.place_order(OrderCreate(
        listing_id=verified_onion_listing.id,
        buyer_name='Sunrise Kirana',
        buyer_type='kirana',
        quantity_kg=20,
        pickup_time='Today 5:30 PM',
        delivery_mode='delivery',
        delivery_address='Lajpat Nagar, Delhi',
    ))

    handover_order = marketplace.place_order(OrderCreate(
        listing_id=verified_tomato_listing.id,
        buyer_name='Asha Retail Mart',
        buyer_type='retailer',
        quantity_kg=18,
        pickup_time='Today 7 PM',
        delivery_mode='delivery',
        delivery_address='South Extension, Delhi',
    ))
    marketplace.respond_to_order(handover_order.id, 'accept')

    in_transit_order = marketplace.place_order(OrderCreate(
        listing_id=verified_onion_listing.id,
        buyer_name='Metro Canteen Services',
        buyer_type='canteen',
        quantity_kg=25,
        pickup_time='Tomorrow 7 AM',
        delivery_mode='delivery',
        delivery_address='Noida Sector 62',
    ))
    marketplace.respond_to_order(in_transit_order.id, 'accept')

    delivered_order = marketplace.place_order(OrderCreate(
        listing_id=verified_tomato_listing.id,
        buyer_name='Sunrise Kirana',
        buyer_type='kirana',
        quantity_kg=12,
        pickup_time='Today 3 PM',
        delivery_mode='delivery',
        delivery_address='Karol Bagh, Delhi',
    ))
    marketplace.respond_to_order(delivered_order.id, 'accept')

    deliveries = marketplace.list_deliveries()
    handover_delivery = next((item for item in deliveries if item.order_id == handover_order.id), None)
    in_transit_delivery = next((item for item in deliveries if item.order_id == in_transit_order.id), None)
    delivered_delivery = next((item for item in deliveries if item.order_id == delivered_order.id), None)

    if handover_delivery is not None:
        marketplace.advance_delivery_for_actor(handover_delivery.id, DeliveryAdvanceRequestIn(next_status='quality_check_pending', actor_role='ops', actor_id='ops-demo-1'))
        marketplace.advance_delivery_for_actor(handover_delivery.id, DeliveryAdvanceRequestIn(next_status='quality_approved', actor_role='ops', actor_id='ops-demo-1'))
        marketplace.advance_delivery_for_actor(handover_delivery.id, DeliveryAdvanceRequestIn(next_status='packed', actor_role='seller', actor_id=handover_delivery.seller_id))
        marketplace.advance_delivery_for_actor(handover_delivery.id, DeliveryAdvanceRequestIn(next_status='handover_pending', actor_role='seller', actor_id=handover_delivery.seller_id))

    if in_transit_delivery is not None:
        marketplace.advance_delivery_for_actor(in_transit_delivery.id, DeliveryAdvanceRequestIn(next_status='quality_check_pending', actor_role='ops', actor_id='ops-demo-1'))
        marketplace.advance_delivery_for_actor(in_transit_delivery.id, DeliveryAdvanceRequestIn(next_status='quality_approved', actor_role='ops', actor_id='ops-demo-1'))
        marketplace.advance_delivery_for_actor(in_transit_delivery.id, DeliveryAdvanceRequestIn(next_status='packed', actor_role='seller', actor_id=in_transit_delivery.seller_id))
        marketplace.advance_delivery_for_actor(in_transit_delivery.id, DeliveryAdvanceRequestIn(next_status='picked_up', actor_role='ops', actor_id='ops-demo-1'))
        marketplace.advance_delivery_for_actor(in_transit_delivery.id, DeliveryAdvanceRequestIn(next_status='in_transit', actor_role='ops', actor_id='ops-demo-1'))

    if delivered_delivery is not None:
        marketplace.advance_delivery_for_actor(delivered_delivery.id, DeliveryAdvanceRequestIn(next_status='quality_check_pending', actor_role='ops', actor_id='ops-demo-1'))
        marketplace.advance_delivery_for_actor(delivered_delivery.id, DeliveryAdvanceRequestIn(next_status='quality_approved', actor_role='ops', actor_id='ops-demo-1'))
        marketplace.advance_delivery_for_actor(delivered_delivery.id, DeliveryAdvanceRequestIn(next_status='packed', actor_role='seller', actor_id=delivered_delivery.seller_id))
        marketplace.advance_delivery_for_actor(delivered_delivery.id, DeliveryAdvanceRequestIn(next_status='picked_up', actor_role='ops', actor_id='ops-demo-1'))
        marketplace.advance_delivery_for_actor(delivered_delivery.id, DeliveryAdvanceRequestIn(next_status='in_transit', actor_role='ops', actor_id='ops-demo-1'))
        marketplace.advance_delivery_for_actor(delivered_delivery.id, DeliveryAdvanceRequestIn(next_status='delivered', actor_role='ops', actor_id='ops-demo-1'))


@router.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@router.post('/demo/seed', response_model=DemoSeedResponse)
def seed_demo(
    store: Any = Depends(get_store),
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> DemoSeedResponse:
    store.reset()
    _seed_demo_demand_pools(store)
    _seed_demo_supply_chain(store, marketplace)
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


@router.get('/demand-pools', response_model=DemandPoolResponse)
def list_demand_pools(marketplace: MarketplaceService = Depends(get_marketplace)) -> DemandPoolResponse:
    return DemandPoolResponse(items=marketplace.build_demand_pools())


@router.get('/sellers/{seller_id}/demand-pools', response_model=DemandPoolResponse)
def list_seller_demand_pools(
    seller_id: str,
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> DemandPoolResponse:
    return DemandPoolResponse(items=marketplace.build_demand_pools())


@router.get('/listings/{listing_id}')
def get_listing(listing_id: str, store: Any = Depends(get_store)) -> dict:
    listing = store.get_listing(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail='Listing not found')
    return listing.model_dump()


@router.post('/delivery/estimate', response_model=DeliveryEstimateResponse)
def estimate_delivery(payload: DeliveryEstimateIn, marketplace: MarketplaceService = Depends(get_marketplace)) -> DeliveryEstimateResponse:
    try:
        return marketplace.estimate_delivery(payload.listing_id, payload.quantity_kg, payload.delivery_address)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/market-prices')
def get_market_prices(
    commodity: str,
    state: str | None = Query(default=None),
    district: str | None = Query(default=None),
    market: str | None = Query(default=None),
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    return {
        'items': [
            item.model_dump(mode='json')
            for item in marketplace.market_price.get_market_prices(
                commodity=commodity,
                state=state,
                district=district,
                market=market,
            )
        ]
    }


@router.get('/listings/{listing_id}/price-intelligence')
def get_listing_price_intelligence(listing_id: str, marketplace: MarketplaceService = Depends(get_marketplace)) -> dict:
    try:
        return marketplace.get_listing_price_intelligence(listing_id).model_dump(mode='json')
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/pricing/suggest')
def suggest_price(payload: PricingSuggestionIn, marketplace: MarketplaceService = Depends(get_marketplace)) -> dict:
    try:
        return marketplace.suggest_price(payload).model_dump(mode='json')
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
def list_notifications(
    role: str | None = Query(default=None),
    recipient_id: str | None = Query(default=None),
    unread_only: bool = Query(default=False),
    store: Any = Depends(get_store),
) -> dict:
    return {'items': store.list_notifications(role=role, recipient_id=recipient_id, unread_only=unread_only)}


@router.post('/notifications/{notification_id}/read')
def mark_notification_read(notification_id: str, store: Any = Depends(get_store)) -> dict:
    item = store.mark_notification_read(notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Notification not found')
    return {'ok': True, 'notification': item}


@router.post('/notifications/read-all')
def mark_all_notifications_read(payload: NotificationReadAllIn, store: Any = Depends(get_store)) -> dict:
    return {'ok': True, 'count': store.mark_all_notifications_read(payload.role, payload.recipient_id)}


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


@router.post('/buyers/demand-requests')
def create_demand_request(
    payload: DemandRequestCreate,
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    request = marketplace.create_demand_request(payload)
    return {'ok': True, 'request': request}


@router.get('/buyers/{buyer_id}/demand-requests')
def list_buyer_demand_requests(
    buyer_id: str,
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    return {'items': marketplace.list_buyer_demand_requests(buyer_id)}


@router.get('/commit-pools')
def list_commit_pools(
    seller_id: str | None = Query(default=None),
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    return {'items': marketplace.list_commit_pools(seller_id=seller_id)}


@router.get('/commit-pools/{pool_id}')
def get_commit_pool(
    pool_id: str,
    store: Any = Depends(get_store),
) -> dict:
    pool = store.get_commit_pool(pool_id)
    if pool is None:
        raise HTTPException(status_code=404, detail='Commit pool not found')
    return pool.model_dump()


@router.post('/commit-pools/{pool_id}/commit')
def commit_pool(
    pool_id: str,
    payload: PoolCommitIn,
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    try:
        result = marketplace.commit_to_pool(pool_id, payload)
        return {'ok': True, **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/deliveries')
def list_deliveries(
    seller_id: str | None = Query(default=None),
    buyer_id: str | None = Query(default=None),
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    return {'items': marketplace.list_deliveries(seller_id=seller_id, buyer_id=buyer_id)}


@router.get('/ops/quality/pending')
def list_ops_pending_quality(marketplace: MarketplaceService = Depends(get_marketplace)) -> dict:
    return {'items': marketplace.list_pending_quality_checks()}


@router.post('/ops/listings/{listing_id}/quality')
def update_ops_listing_quality(
    listing_id: str,
    payload: ListingQualityUpdateIn,
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    try:
        return {'ok': True, 'listing': marketplace.update_listing_quality(listing_id, payload)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/ops/deliveries')
def list_ops_deliveries(marketplace: MarketplaceService = Depends(get_marketplace)) -> dict:
    return {'items': marketplace.list_deliveries()}


@router.get('/ops/delivery-partners')
def list_ops_delivery_partners(marketplace: MarketplaceService = Depends(get_marketplace)) -> dict:
    return {'items': [partner.model_dump(mode='json') for partner in marketplace.list_delivery_partners()]}


@router.post('/ops/deliveries/{delivery_id}/advance')
def advance_ops_delivery(
    delivery_id: str,
    payload: DeliveryAdvanceRequestIn,
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    try:
        return {'ok': True, 'delivery': marketplace.advance_delivery_for_actor(delivery_id, payload)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/ops/deliveries/{delivery_id}/assign-partner')
def assign_ops_delivery_partner(
    delivery_id: str,
    payload: DeliveryPartnerAssignIn,
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    try:
        return {'ok': True, 'delivery': marketplace.reassign_delivery_partner(delivery_id, payload.partner_id, payload.assigned_by)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/ops/dashboard')
def get_ops_dashboard(marketplace: MarketplaceService = Depends(get_marketplace)) -> dict:
    return marketplace.build_ops_dashboard().model_dump()


@router.get('/ops/metrics')
def get_ops_metrics(marketplace: MarketplaceService = Depends(get_marketplace)) -> dict:
    return marketplace.build_ops_metrics().model_dump()


@router.post('/deliveries/{delivery_id}/advance')
def advance_delivery(
    delivery_id: str,
    payload: DeliveryAdvanceIn,
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    try:
        return {'ok': True, 'delivery': marketplace.advance_delivery(delivery_id, payload.status, actor_role='seller')}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/buyers/deliveries/{delivery_id}/confirm')
def confirm_buyer_delivery(
    delivery_id: str,
    payload: BuyerDeliveryConfirmIn,
    marketplace: MarketplaceService = Depends(get_marketplace),
) -> dict:
    try:
        return {'ok': True, 'delivery': marketplace.confirm_buyer_delivery(delivery_id, payload)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

