from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
import hashlib

import httpx

from app.config import get_settings
from app.schemas import BuyerDemandEvent, BuyerDemandSearchIn, BuyerDemandSearchResponse, BuyerDeliveryConfirmIn, CommitDemandPool, Delivery, DeliveryAdvanceRequestIn, DeliveryEstimateResponse, DemandPoolOpportunity, DemandRequest, DemandRequestCreate, LedgerCaptureMode, LedgerEntry, LedgerPaymentCreate, LedgerSummary, Listing, ListingCreate, ListingQualityUpdateIn, MarketPriceReference, NotificationRecord, NotificationRecipientRole, OpsDashboardResponse, OpsMetricSnapshot, Order, OrderCreate, PoolCommitIn, PoolMember, PricingSuggestionIn, ProduceQualityAssessment, SellerDashboard, SellerLedgerView, SellerNotification, SellerProfile, SourceChannel
from app.services.extraction import ExtractionService
from app.services.geo_service import GeoService
from app.services.market_price_service import MarketPriceService
from app.services.speech_service import SpeechService
from app.services.store import JsonStore
from app.services.whatsapp_service import WhatsAppService


class MarketplaceService:
    def __init__(self, store: JsonStore):
        self.store = store
        self.settings = get_settings()
        self.extractor = ExtractionService()
        self.speech = SpeechService()
        self.geo = GeoService()
        self.market_price = MarketPriceService()
        self.whatsapp = WhatsAppService()

    def _public_image_url(self, image_url: str | None) -> str | None:
        if image_url and image_url.startswith(('http://', 'https://')):
            return image_url
        return None

    def _price_intelligence_for_listing(
        self,
        *,
        product_name: str,
        quality_grade: str | None,
        seller_price_per_kg: float | None,
        pickup_location: str | None,
    ) -> MarketPriceReference | None:
        try:
            return self.market_price.suggest_listing_price(
                product_name=product_name,
                quality_grade=quality_grade,
                seller_price=seller_price_per_kg,
                pickup_location=pickup_location,
            )
        except Exception:
            return None

    def _compute_delivery_estimate(
        self,
        *,
        listing: Listing,
        quantity_kg: float,
        delivery_address: str,
    ) -> DeliveryEstimateResponse:
        normalized_address = delivery_address.strip()
        geocoded = self.geo.geocode(normalized_address)
        buyer_lat = geocoded.get('latitude') if geocoded else None
        buyer_lng = geocoded.get('longitude') if geocoded else None
        normalized_address = geocoded.get('pickup_location') if geocoded and geocoded.get('pickup_location') else normalized_address

        profile = self.store.get_seller_profile(listing.seller_id)
        seller_lat = profile.latitude if (profile and profile.latitude is not None) else listing.latitude
        seller_lng = profile.longitude if (profile and profile.longitude is not None) else listing.longitude
        seller_pickup_location = (profile.default_pickup_location if profile and profile.default_pickup_location else listing.pickup_location)

        distance_km, distance_source = self.geo.resolve_distance(
            origin_address=seller_pickup_location,
            destination_address=normalized_address,
            origin_lat=seller_lat,
            origin_lng=seller_lng,
            destination_lat=buyer_lat,
            destination_lng=buyer_lng,
        )
        breakdown = self.geo.estimate_delivery_breakdown(
            quantity_kg=quantity_kg,
            distance_km=distance_km,
            distance_source=distance_source,
        )
        return DeliveryEstimateResponse(
            listing_id=listing.id,
            seller_id=listing.seller_id,
            seller_pickup_location=seller_pickup_location,
            delivery_address=normalized_address,
            quantity_kg=quantity_kg,
            distance_km=breakdown.distance_km,
            distance_source=breakdown.distance_source,
            base_fee=breakdown.base_fee,
            distance_fee=breakdown.distance_fee,
            weight_fee=breakdown.weight_fee,
            surge_fee=breakdown.surge_fee,
            total_delivery_fee=breakdown.total_delivery_fee,
            currency=breakdown.currency,
            fee_label=breakdown.fee_label,
            pricing_notes=breakdown.pricing_notes,
        )

    def estimate_delivery(self, listing_id: str, quantity_kg: float, delivery_address: str) -> DeliveryEstimateResponse:
        listing = self.store.get_listing(listing_id)
        if listing is None:
            raise ValueError('Listing not found')
        return self._compute_delivery_estimate(listing=listing, quantity_kg=quantity_kg, delivery_address=delivery_address)

    def add_role_notification(
        self,
        *,
        recipient_role: NotificationRecipientRole,
        recipient_id: str | None,
        category: str,
        title: str,
        text: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        action_label: str | None = None,
        action_target: str | None = None,
        channel: str = 'web',
        delivery_status: str = 'simulated',
        audio_base64: str | None = None,
        seller_id: str | None = None,
        order_id: str | None = None,
    ) -> NotificationRecord:
        notification = NotificationRecord(
            recipient_role=recipient_role,
            recipient_id=recipient_id,
            seller_id=seller_id,
            order_id=order_id,
            category=category,  # type: ignore[arg-type]
            title=title,
            text=text,
            body=text,
            entity_type=entity_type,
            entity_id=entity_id,
            action_label=action_label,
            action_target=action_target,
            channel=channel,
            delivery_status=delivery_status,
            audio_base64=audio_base64,
        )
        self.store.add_notification(notification.model_dump(mode='json'))
        return notification

    def notify_buyer(self, recipient_id: str | None, **kwargs) -> NotificationRecord:
        return self.add_role_notification(recipient_role='buyer', recipient_id=recipient_id, **kwargs)

    def notify_seller(self, recipient_id: str | None, **kwargs) -> NotificationRecord:
        return self.add_role_notification(recipient_role='seller', recipient_id=recipient_id, **kwargs)

    def notify_ops(self, **kwargs) -> NotificationRecord:
        return self.add_role_notification(recipient_role='ops', recipient_id='ops-team', **kwargs)

    def listing_image_url(
        self,
        image_url: str | None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
    ) -> str | None:
        return self._public_image_url(image_url) or self._persist_listing_image(image_bytes, image_mime_type)

    def _persist_listing_image(self, image_bytes: bytes | None, image_mime_type: str | None) -> str | None:
        if not image_bytes or not image_mime_type:
            return None

        extension_by_mime = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/webp': 'webp',
            'image/gif': 'gif',
        }
        content_type = image_mime_type.split(';', 1)[0].strip().lower()
        extension = extension_by_mime.get(content_type)
        if extension is None:
            return None

        media_dir = self.settings.media_dir / 'listings'
        media_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(image_bytes).hexdigest()[:24]
        filename = f'{digest}.{extension}'
        target = media_dir / filename
        if not target.exists():
            target.write_bytes(image_bytes)

        return f'{self.settings.api_public_base_url.rstrip("/")}/media/listings/{filename}'

    def _fetch_public_image_bytes(self, image_url: str | None) -> tuple[bytes | None, str | None]:
        public_image_url = self._public_image_url(image_url)
        if not public_image_url:
            return None, None

        try:
            response = httpx.get(public_image_url, timeout=20.0)
            response.raise_for_status()
        except httpx.HTTPError:
            return None, None

        return response.content, response.headers.get('content-type')

    def assess_produce_image(
        self,
        *,
        image_bytes: bytes | None,
        image_mime_type: str | None,
        image_url: str | None = None,
        product_hint: str | None = None,
    ) -> ProduceQualityAssessment | None:
        candidate_bytes = image_bytes
        candidate_mime_type = image_mime_type
        if not candidate_bytes:
            candidate_bytes, candidate_mime_type = self._fetch_public_image_bytes(image_url)
        if not candidate_bytes or not candidate_mime_type:
            return None
        return self.extractor.assess_produce_image(
            image_bytes=candidate_bytes,
            mime_type=candidate_mime_type,
            product_hint=product_hint,
        )

    def create_listing_from_message(
        self,
        *,
        seller_id: str,
        seller_name: str,
        message_text: str,
        image_url: str | None,
        source_channel: SourceChannel = 'api',
        default_pickup_location: str | None = None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        quality_assessment: ProduceQualityAssessment | None = None,
    ) -> Listing:
        public_image_url = self.listing_image_url(image_url, image_bytes, image_mime_type)
        effective_quality_assessment = quality_assessment or self.assess_produce_image(
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            image_url=public_image_url,
        )

        draft: ListingCreate = self.extractor.extract_listing(
            message=message_text,
            seller_id=seller_id,
            seller_name=seller_name,
            image_url=public_image_url,
            source_channel=source_channel,
            default_pickup_location=default_pickup_location,
            quality_assessment=effective_quality_assessment,
        )

        geocoded = self.geo.geocode(draft.pickup_location)
        if geocoded:
            draft.pickup_location = geocoded['pickup_location']
            draft.latitude = geocoded.get('latitude')
            draft.longitude = geocoded.get('longitude')
            draft.place_id = geocoded.get('place_id')

        listing = Listing(
            seller_id=draft.seller_id,
            seller_name=draft.seller_name,
            product_name=draft.product_name,
            category=draft.category,
            quantity_kg=draft.quantity_kg,
            available_kg=draft.quantity_kg,
            price_per_kg=draft.price_per_kg,
            pickup_location=draft.pickup_location,
            quality_grade=draft.quality_grade,
            quality_score=draft.quality_score,
            quality_summary=draft.quality_summary,
            quality_assessment_source=draft.quality_assessment_source,
            quality_signals=draft.quality_signals,
            quality_status='pending',
            quality_confidence=(
                round(draft.quality_score / 100, 2)
                if draft.quality_score is not None
                else None
            ),
            quality_notes=(
                f'AI preliminary assessment: {draft.quality_summary}'
                if draft.quality_assessment_source == 'ai_visual' and draft.quality_summary
                else None
            ),
            quality_proof_images=[str(draft.image_url)] if draft.image_url else [],
            verified_by_bolbazaar=False,
            image_url=draft.image_url,
            description=draft.description,
            tags=draft.tags,
            latitude=draft.latitude,
            longitude=draft.longitude,
            place_id=draft.place_id,
            market_reference_price_per_kg=draft.market_reference_price_per_kg,
            suggested_price_per_kg=draft.suggested_price_per_kg,
            price_intelligence_note=draft.price_intelligence_note,
            price_intelligence_source=draft.price_intelligence_source,
            price_intelligence_updated_at=draft.price_intelligence_updated_at,
            source_channel=draft.source_channel,
            raw_message=draft.raw_message,
            freshness_label='AI photo checked' if draft.quality_assessment_source == 'ai_visual' else 'Fresh today',
        )
        price_reference = self._price_intelligence_for_listing(
            product_name=listing.product_name,
            quality_grade=listing.quality_grade,
            seller_price_per_kg=listing.price_per_kg,
            pickup_location=listing.pickup_location,
        )
        if price_reference is not None:
            listing.market_reference_price_per_kg = price_reference.mandi_modal_price_per_kg
            listing.suggested_price_per_kg = price_reference.suggested_price_per_kg
            listing.price_intelligence_note = price_reference.explanation
            listing.price_intelligence_source = price_reference.data_source
            listing.price_intelligence_updated_at = price_reference.fetched_at
        saved_listing = self.store.save_listing(listing)

        profile = self.store.get_seller_profile(seller_id)
        quality_text = ''
        if saved_listing.quality_assessment_source == 'ai_visual':
            grade_text = saved_listing.quality_grade.title()
            if saved_listing.quality_score is not None:
                quality_text = f' AI quality grade: {grade_text} ({saved_listing.quality_score}/100).'
            else:
                quality_text = f' AI quality grade: {grade_text}.'
        if profile is not None and profile.preferred_language == 'hi':
            confirmation_text = (
                f'आपकी लिस्टिंग लाइव हो गई है। {saved_listing.product_name}, '
                f'{saved_listing.available_kg} किलो, Rs {saved_listing.price_per_kg} प्रति किलो।'
            )
            if quality_text:
                confirmation_text += quality_text.replace('AI quality grade', 'AI गुणवत्ता ग्रेड')
        else:
            confirmation_text = (
                f'Your listing is live. {saved_listing.product_name}, '
                f'{saved_listing.available_kg} kg, Rs {saved_listing.price_per_kg} per kg.'
            ) + quality_text
        if price_reference is not None and price_reference.mandi_modal_price_per_kg is not None:
            if profile is not None and profile.preferred_language == 'hi':
                confirmation_text += (
                    f' मंडी रेफरेंस लगभग Rs {price_reference.mandi_modal_price_per_kg}/किलो है। '
                    f'सुझाई गई रेंज Rs {price_reference.suggested_min_price_per_kg}-Rs {price_reference.suggested_max_price_per_kg}/किलो।'
                )
            else:
                confirmation_text += (
                    f' Mandi reference is about Rs {price_reference.mandi_modal_price_per_kg}/kg. '
                    f'Suggested range: Rs {price_reference.suggested_min_price_per_kg}-Rs {price_reference.suggested_max_price_per_kg}/kg.'
                )
        try:
            whatsapp_result = self.whatsapp.send_text_message(to=seller_id, body=confirmation_text)
        except Exception as exc:  # pragma: no cover - network failures depend on runtime
            whatsapp_result = {'sent': False, 'reason': 'send_failed', 'error': str(exc)}

        try:
            audio_base64 = self.speech.synthesize(confirmation_text)
        except Exception:  # pragma: no cover - cloud TTS failures depend on runtime
            audio_base64 = None

        self.notify_seller(
            recipient_id=seller_id,
            seller_id=seller_id,
            order_id='listing_confirmation',
            category='pricing' if price_reference is not None else 'system',
            title='Listing created',
            text=confirmation_text,
            entity_type='listing',
            entity_id=saved_listing.id,
            action_label='View listing',
            action_target='listings',
            channel='whatsapp',
            delivery_status=self.whatsapp.delivery_status(whatsapp_result),
            audio_base64=audio_base64,
        )
        self.notify_ops(
            category='quality',
            title='Listing pending quality review',
            text=f'{saved_listing.product_name} from {saved_listing.seller_name} is awaiting ops review.',
            entity_type='listing',
            entity_id=saved_listing.id,
            action_label='Review lot',
            action_target='quality',
            seller_id=seller_id,
            order_id='listing_confirmation',
        )
        return saved_listing

    def list_live_listings(self) -> list[Listing]:
        items = [listing for listing in self.store.list_listings() if listing.status == 'live']
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def get_listing_price_intelligence(self, listing_id: str) -> MarketPriceReference:
        listing = self.store.get_listing(listing_id)
        if listing is None:
            raise ValueError('Listing not found')
        reference = self._price_intelligence_for_listing(
            product_name=listing.product_name,
            quality_grade=listing.quality_grade,
            seller_price_per_kg=listing.price_per_kg,
            pickup_location=listing.pickup_location,
        )
        if reference is None:
            raise ValueError('Price intelligence unavailable')
        return reference

    def suggest_price(self, payload: PricingSuggestionIn) -> MarketPriceReference:
        reference = self.market_price.suggest_listing_price(
            product_name=payload.product_name,
            quality_grade=payload.quality_grade,
            seller_price=payload.seller_price_per_kg,
            pickup_location=payload.pickup_location,
        )
        if reference is None:
            raise ValueError('Price intelligence unavailable')
        return reference

    def list_seller_profiles(self) -> list[SellerProfile]:
        profiles = self.store.list_seller_profiles()
        return sorted(profiles, key=lambda item: item.updated_at, reverse=True)

    def list_ledger_entries(self, seller_id: str | None = None) -> list[LedgerEntry]:
        list_entries = getattr(self.store, 'list_ledger_entries', None)
        if list_entries is None:
            return []

        entries = list_entries()
        if seller_id is not None:
            entries = [entry for entry in entries if entry.seller_id == seller_id]
        return sorted(entries, key=lambda item: item.created_at, reverse=True)

    def _normalize_product_name(self, product_name: str | None) -> str:
        return ' '.join((product_name or '').strip().lower().split())

    def _format_amount(self, value: float | None) -> str:
        return f'{value:g}' if value is not None else '0'

    def _build_sale_entry_summary(self, entry: LedgerEntry, total_amount: float, amount_due: float) -> str:
        details: list[str] = []
        if entry.product_name and entry.quantity_kg is not None:
            details.append(f'bought {self._format_amount(entry.quantity_kg)} kg {entry.product_name}')
        elif entry.product_name:
            details.append(f'bought {entry.product_name}')
        else:
            details.append('made a purchase')
        details.append(f'Total Rs {self._format_amount(total_amount)}')
        if entry.amount_paid > 0:
            details.append(f'paid Rs {self._format_amount(entry.amount_paid)}')
        if amount_due > 0:
            details.append(f'due Rs {self._format_amount(amount_due)}')
        return f'{entry.buyer_name} {", ".join(details)}.'

    def _resolve_ledger_entries(self, seller_id: str) -> list[LedgerEntry]:
        entries = self.list_ledger_entries(seller_id)
        latest_listing_by_product: dict[str, Listing] = {}
        for listing in self.store.list_listings():
            if listing.seller_id != seller_id:
                continue
            product_key = self._normalize_product_name(listing.product_name)
            if not product_key:
                continue
            current = latest_listing_by_product.get(product_key)
            if current is None or listing.created_at > current.created_at:
                latest_listing_by_product[product_key] = listing

        resolved_entries: list[LedgerEntry] = []
        for entry in entries:
            if entry.entry_kind != 'sale' or entry.quantity_kg is None:
                resolved_entries.append(entry)
                continue

            product_key = self._normalize_product_name(entry.product_name)
            listing = latest_listing_by_product.get(product_key)
            if listing is None:
                resolved_entries.append(entry)
                continue

            recomputed_total = round(entry.quantity_kg * listing.price_per_kg, 2)
            normalized_total = max(recomputed_total, round(entry.amount_paid, 2))
            normalized_due = max(round(normalized_total - entry.amount_paid, 2), 0.0)
            if (
                entry.total_amount == normalized_total
                and entry.amount_due == normalized_due
                and entry.balance_delta == normalized_due
            ):
                resolved_entries.append(entry)
                continue

            resolved_entries.append(entry.model_copy(update={
                'total_amount': normalized_total,
                'amount_due': normalized_due,
                'balance_delta': normalized_due,
                'summary': self._build_sale_entry_summary(entry, normalized_total, normalized_due),
            }))
        return resolved_entries

    def _normalize_search_query(self, query: str) -> str:
        normalized = ' '.join(query.strip().lower().split())
        if not normalized:
            return ''

        normalize_message = getattr(self.extractor, '_normalize_message', None)
        if callable(normalize_message):
            try:
                candidate = normalize_message(query)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate
            except Exception:
                return normalized
        return normalized

    def _demand_alert_fingerprint(self, seller_id: str, product_name: str) -> str:
        payload = f'demand_push|{seller_id}|{product_name.strip().lower()}'
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def _format_demand_push_message(
        self,
        profile: SellerProfile,
        product_name: str,
        buyer_count: int,
        pool: DemandPoolOpportunity | None = None,
    ) -> str:
        seller_name = (profile.seller_name or 'Seller').strip()
        quantity_line = ''
        pricing_line = ''
        if pool is not None:
            quantity = f'{pool.total_quantity_kg:g}'
            location = pool.delivery_locations[0] if pool.delivery_locations else None
            if profile.preferred_language == 'hi':
                quantity_line = f' कुल मांग लगभग {quantity} किलो है'
                if location:
                    quantity_line += f' ({location})'
                quantity_line += '.'
            else:
                quantity_line = f' Total pooled demand is about {quantity} kg'
                if location:
                    quantity_line += f' near {location}'
                quantity_line += '.'
            reference = pool.market_price_reference
            if reference is not None and reference.mandi_modal_price_per_kg is not None:
                if profile.preferred_language == 'hi':
                    pricing_line = (
                        f' मंडी modal भाव लगभग Rs {reference.mandi_modal_price_per_kg}/किलो है।'
                        f' सुझाया selling price Rs {reference.suggested_min_price_per_kg}-Rs {reference.suggested_max_price_per_kg}/किलो।'
                    )
                else:
                    pricing_line = (
                        f' Latest mandi reference is Rs {reference.mandi_modal_price_per_kg}/kg modal.'
                        f' Suggested seller price: Rs {reference.suggested_min_price_per_kg}-Rs {reference.suggested_max_price_per_kg}/kg.'
                    )
        if profile.preferred_language == 'hi':
            return (
                f'नमस्ते {seller_name}, अभी {buyer_count} खरीदार {product_name} ढूंढ रहे हैं। '
                f'{quantity_line}{pricing_line} जल्दी बेचने के लिए अभी लिस्ट करें।'
            )
        return (
            f'Hi {seller_name}, {buyer_count} buyers are looking for {product_name} right now. '
            f'{quantity_line}{pricing_line} List now to sell faster.'
        )

    def build_demand_pools(self, window_minutes: int | None = None) -> list[DemandPoolOpportunity]:
        list_events = getattr(self.store, 'list_buyer_search_events', None)
        if not callable(list_events):
            return []

        effective_window = window_minutes or self.settings.demand_push_window_minutes
        since = datetime.utcnow() - timedelta(minutes=effective_window)
        recent_events = list_events(since=since)

        grouped: dict[str, list[BuyerDemandEvent]] = {}
        for event in recent_events:
            if not event.detected_product_name or not event.detected_product_name.strip():
                continue
            normalized_product = event.detected_product_name.strip().lower()
            grouped.setdefault(normalized_product, []).append(event)

        pools: list[DemandPoolOpportunity] = []
        for normalized_product, events in grouped.items():
            product_name = events[0].detected_product_name or normalized_product.title()
            category = events[0].detected_category

            buyer_ids = {
                event.buyer_id.strip().lower()
                for event in events
                if event.buyer_id and event.buyer_id.strip()
            }

            explicit_quantity_total = sum(event.quantity_kg or 0 for event in events)
            buyers_with_explicit_quantity = {
                event.buyer_id.strip().lower()
                for event in events
                if event.quantity_kg and event.buyer_id and event.buyer_id.strip()
            }

            # For demo-friendly pooling, missing buyer quantities are estimated at 10 kg
            # per unique buyer so fragmented search demand still surfaces as a visible opportunity.
            estimated_missing_quantity = max(len(buyer_ids - buyers_with_explicit_quantity), 0) * 10
            total_quantity_kg = explicit_quantity_total + estimated_missing_quantity

            price_points = [event.max_price_per_kg for event in events if event.max_price_per_kg is not None]
            average_max_price = round(sum(price_points) / len(price_points), 2) if price_points else None
            min_max_price = min(price_points) if price_points else None
            max_max_price = max(price_points) if price_points else None

            delivery_locations = list(dict.fromkeys(
                event.delivery_location.strip()
                for event in events
                if event.delivery_location and event.delivery_location.strip()
            ))
            needed_by_labels = list(dict.fromkeys(
                event.needed_by.strip()
                for event in events
                if event.needed_by and event.needed_by.strip()
            ))
            buyer_types = list(dict.fromkeys(
                event.buyer_type.strip()
                for event in events
                if event.buyer_type and event.buyer_type.strip()
            ))

            slug = ''.join(char if char.isalnum() else '_' for char in normalized_product).strip('_') or 'produce'
            pool_hash = hashlib.sha256(normalized_product.encode('utf-8')).hexdigest()[:8]
            formatted_quantity = f'{round(total_quantity_kg, 1):g}'
            unique_buyer_count = len(buyer_ids)
            urgency_label = 'High demand' if unique_buyer_count >= self.settings.demand_push_threshold else 'Emerging demand'
            market_reference = self.market_price.get_best_market_reference(
                product_name,
                pickup_location=delivery_locations[0] if delivery_locations else None,
            )
            suggested_action = f'Create a matching {product_name} listing for {formatted_quantity} kg demand from {unique_buyer_count} buyers.'
            if market_reference is not None and market_reference.mandi_modal_price_per_kg is not None:
                suggested_action += (
                    f' Latest mandi modal is Rs {market_reference.mandi_modal_price_per_kg}/kg'
                    f' with suggested seller range Rs {market_reference.suggested_min_price_per_kg}-Rs {market_reference.suggested_max_price_per_kg}/kg.'
                )

            pools.append(
                DemandPoolOpportunity(
                    id=f'pool_{slug}_{pool_hash}',
                    product_name=product_name,
                    category=category,
                    total_quantity_kg=round(total_quantity_kg, 2),
                    unique_buyer_count=unique_buyer_count,
                    average_max_price_per_kg=average_max_price,
                    min_max_price_per_kg=min_max_price,
                    max_max_price_per_kg=max_max_price,
                    delivery_locations=delivery_locations,
                    needed_by_labels=needed_by_labels,
                    buyer_types=buyer_types,
                    window_minutes=effective_window,
                    created_from_event_ids=[event.id for event in events],
                    suggested_action=suggested_action,
                    urgency_label=urgency_label,
                    market_price_reference=market_reference,
                )
            )

        return sorted(
            pools,
            key=lambda item: (item.unique_buyer_count, item.total_quantity_kg),
            reverse=True,
        )

    def process_buyer_demand_search(self, payload: BuyerDemandSearchIn) -> BuyerDemandSearchResponse:
        normalized_query = self._normalize_search_query(payload.search_query)
        signals = self.extractor.parse_listing_signals(payload.search_query)
        detected_product_name = signals.get('product_name')
        detected_category = signals.get('category')
        if detected_category not in {'vegetables', 'fruits', 'grains', 'spices', 'other'}:
            detected_category = None

        event = BuyerDemandEvent(
            buyer_id=payload.buyer_id,
            search_query=payload.search_query,
            normalized_query=normalized_query,
            detected_product_name=detected_product_name,
            detected_category=detected_category,
            max_price_per_kg=payload.max_price_per_kg,
            quantity_kg=payload.quantity_kg,
            delivery_location=payload.delivery_location,
            needed_by=payload.needed_by,
            buyer_type=payload.buyer_type,
            source_channel='api',
        )

        save_event = getattr(self.store, 'save_buyer_search_event', None)
        if callable(save_event):
            save_event(event)

        threshold = self.settings.demand_push_threshold
        if not detected_product_name:
            return BuyerDemandSearchResponse(
                event_id=event.id,
                detected_product_name=None,
                detected_category=None,
                unique_buyer_count=0,
                threshold=threshold,
                threshold_reached=False,
                notified_seller_count=0,
                reason='unsupported_query',
            )

        list_events = getattr(self.store, 'list_buyer_search_events', None)
        if not callable(list_events):
            return BuyerDemandSearchResponse(
                event_id=event.id,
                detected_product_name=detected_product_name,
                detected_category=detected_category,
                unique_buyer_count=0,
                threshold=threshold,
                threshold_reached=False,
                notified_seller_count=0,
                reason='demand_storage_unavailable',
            )

        since = datetime.utcnow() - timedelta(minutes=self.settings.demand_push_window_minutes)
        recent_events = list_events(since=since, detected_product_name=detected_product_name)
        unique_buyers = {
            item.buyer_id.strip().lower()
            for item in recent_events
            if item.buyer_id and item.buyer_id.strip()
        }
        unique_buyer_count = len(unique_buyers)
        if unique_buyer_count < threshold:
            return BuyerDemandSearchResponse(
                event_id=event.id,
                detected_product_name=detected_product_name,
                detected_category=detected_category,
                unique_buyer_count=unique_buyer_count,
                threshold=threshold,
                threshold_reached=False,
                notified_seller_count=0,
                reason='below_threshold',
            )

        claim_fingerprint = getattr(self.store, 'claim_demand_alert_fingerprint', None)
        mark_fingerprint = getattr(self.store, 'mark_demand_alert_fingerprint_processed', None)
        release_fingerprint = getattr(self.store, 'release_demand_alert_fingerprint', None)

        cooldown_seconds = self.settings.demand_push_cooldown_minutes * 60
        matching_pool = next(
            (pool for pool in self.build_demand_pools() if pool.product_name.strip().lower() == detected_product_name.strip().lower()),
            None,
        )
        active_sellers = [
            profile
            for profile in self.list_seller_profiles()
            if profile.registration_status == 'active'
        ]

        notified_seller_count = 0
        for profile in active_sellers:
            fingerprint = self._demand_alert_fingerprint(profile.seller_id, detected_product_name)
            if callable(claim_fingerprint):
                can_send = claim_fingerprint(fingerprint, window_seconds=cooldown_seconds)
                if not can_send:
                    continue

            message_text = self._format_demand_push_message(profile, detected_product_name, unique_buyer_count, matching_pool)
            try:
                whatsapp_result = self.whatsapp.send_text_message(to=profile.seller_id, body=message_text)
            except Exception as exc:  # pragma: no cover - network failures depend on runtime
                whatsapp_result = {'sent': False, 'reason': 'send_failed', 'error': str(exc)}

            if whatsapp_result.get('sent'):
                notified_seller_count += 1
                if callable(mark_fingerprint):
                    mark_fingerprint(fingerprint)
            elif callable(release_fingerprint):
                release_fingerprint(fingerprint)

            self.notify_seller(
                recipient_id=profile.seller_id,
                seller_id=profile.seller_id,
                order_id=f'demand_push:{event.id}',
                category='demand',
                title='Demand threshold reached',
                text=message_text,
                entity_type='demand',
                entity_id=event.id,
                action_label='View demand pools',
                action_target='demand',
                channel='whatsapp',
                delivery_status=self.whatsapp.delivery_status(whatsapp_result),
            )

        reason = None
        if not active_sellers:
            reason = 'no_active_sellers'
        elif notified_seller_count == 0:
            reason = 'cooldown_active_or_delivery_failed'

        return BuyerDemandSearchResponse(
            event_id=event.id,
            detected_product_name=detected_product_name,
            detected_category=detected_category,
            unique_buyer_count=unique_buyer_count,
            threshold=threshold,
            threshold_reached=True,
            notified_seller_count=notified_seller_count,
            reason=reason,
        )

    def _build_ledger_summary(self, seller_id: str) -> LedgerSummary:
        entries = self._resolve_ledger_entries(seller_id)
        buyer_balances: dict[str, float] = {}
        for entry in entries:
            buyer_balances[entry.buyer_name] = round(buyer_balances.get(entry.buyer_name, 0.0) + entry.balance_delta, 2)

        return LedgerSummary(
            total_entries=len(entries),
            total_outstanding_amount=round(sum(max(balance, 0.0) for balance in buyer_balances.values()), 2),
            total_collected_amount=round(sum(entry.amount_paid for entry in entries), 2),
            buyers_with_balance=sum(1 for balance in buyer_balances.values() if balance > 0),
            recent_entries=entries[:5],
        )

    def build_seller_ledger(self, seller_id: str) -> SellerLedgerView | None:
        profile = self.store.get_seller_profile(seller_id)
        if profile is None:
            return None

        entries = self._resolve_ledger_entries(seller_id)
        return SellerLedgerView(
            seller_id=seller_id,
            summary=self._build_ledger_summary(seller_id),
            items=entries[:20],
        )

    def record_ledger_entry_from_message(
        self,
        *,
        seller_id: str,
        message_text: str,
        source_channel: SourceChannel = 'whatsapp',
        capture_mode: LedgerCaptureMode = 'text_message',
    ) -> LedgerEntry | None:
        entry = self.extractor.extract_ledger_entry(
            message=message_text,
            seller_id=seller_id,
            source_channel=source_channel,
            capture_mode=capture_mode,
        )
        if entry is None:
            return None

        save_entry = getattr(self.store, 'save_ledger_entry', None)
        if save_entry is None:
            return None
        return save_entry(entry)

    def record_ledger_payment(
        self,
        *,
        seller_id: str,
        payload: LedgerPaymentCreate,
        source_channel: SourceChannel = 'api',
    ) -> LedgerEntry:
        profile = self.store.get_seller_profile(seller_id)
        if profile is None:
            raise ValueError('Seller not found')

        buyer_name = payload.buyer_name.strip()
        amount_paid = round(payload.amount_paid, 2)
        note = (payload.notes or '').strip() or None
        summary = f'{buyer_name} paid Rs {amount_paid:g} toward the khata balance.'
        if note:
            summary = f'{summary} {note}'

        entry = LedgerEntry(
            seller_id=seller_id,
            buyer_name=buyer_name,
            entry_kind='payment',
            amount_paid=amount_paid,
            amount_due=0,
            balance_delta=-amount_paid,
            summary=summary,
            notes=note,
            source_channel=source_channel,
            capture_mode='text_message',
            parse_source='rule_based',
            raw_message=summary,
        )

        save_entry = getattr(self.store, 'save_ledger_entry', None)
        if save_entry is None:
            raise ValueError('Ledger storage unavailable')
        return save_entry(entry)

    def build_seller_dashboard(self, seller_id: str) -> SellerDashboard | None:
        profile = self.store.get_seller_profile(seller_id)
        if profile is None:
            return None

        listings = [item for item in self.store.list_listings() if item.seller_id == seller_id]
        live_listings = [item for item in listings if item.status == 'live']
        orders = [item for item in self.store.list_orders() if item.seller_id == seller_id]
        accepted_orders = [item for item in orders if item.status in {'accepted', 'completed'}]

        today = datetime.utcnow().date()
        todays_orders = [item for item in accepted_orders if item.created_at.date() == today]
        customer_counts = Counter(item.buyer_name for item in accepted_orders)
        recent_customers = list(dict.fromkeys(
            item.buyer_name
            for item in sorted(accepted_orders, key=lambda order: order.created_at, reverse=True)
        ))
        ledger_summary = self._build_ledger_summary(seller_id)
        recent_price_intelligence = []
        for item in sorted(live_listings, key=lambda listing: listing.price_intelligence_updated_at or listing.created_at, reverse=True):
            if item.market_reference_price_per_kg is None:
                continue
            recent_price_intelligence.append(
                MarketPriceReference(
                    product_name=item.product_name,
                    normalized_commodity=item.product_name,
                    market=item.pickup_location,
                    mandi_modal_price_per_kg=item.market_reference_price_per_kg,
                    data_source=item.price_intelligence_source or 'demo_fallback',
                    suggested_price_per_kg=item.suggested_price_per_kg,
                    suggested_min_price_per_kg=item.suggested_price_per_kg,
                    suggested_max_price_per_kg=item.suggested_price_per_kg,
                    explanation=item.price_intelligence_note or 'Recent mandi reference available.',
                    fetched_at=item.price_intelligence_updated_at or item.created_at,
                )
            )

        return SellerDashboard(
            seller_id=profile.seller_id,
            seller_name=profile.seller_name,
            store_name=profile.store_name,
            preferred_language=profile.preferred_language,
            default_pickup_location=profile.default_pickup_location,
            live_listings_count=len(live_listings),
            total_available_kg=round(sum(item.available_kg for item in live_listings), 2),
            sold_today_kg=round(sum(item.quantity_kg for item in todays_orders), 2),
            sold_today_revenue=round(sum(item.total_price for item in todays_orders), 2),
            total_customers=len(customer_counts),
            repeat_customers=sum(1 for count in customer_counts.values() if count > 1),
            pending_orders=len([item for item in orders if item.status == 'pending']),
            ledger_entries_count=ledger_summary.total_entries,
            ledger_outstanding_amount=ledger_summary.total_outstanding_amount,
            ledger_collected_amount=ledger_summary.total_collected_amount,
            ledger_buyers_with_balance=ledger_summary.buyers_with_balance,
            recent_customers=recent_customers[:5],
            recent_listings=sorted(live_listings, key=lambda item: item.created_at, reverse=True)[:5],
            recent_ledger_entries=ledger_summary.recent_entries,
            recent_price_intelligence=recent_price_intelligence[:5],
        )

    LEGACY_DELIVERY_STATUS_MAP = {
        'accepted': 'order_accepted',
        'out_for_delivery': 'in_transit',
    }

    CANONICAL_DELIVERY_STATUS_MAP = {
        'pending': 'pending',
        'accepted': 'order_accepted',
        'order_accepted': 'order_accepted',
        'quality_check_pending': 'quality_check_pending',
        'quality_approved': 'quality_approved',
        'quality_rejected': 'quality_rejected',
        'packed': 'packed',
        'handover_pending': 'handover_pending',
        'picked_up': 'picked_up',
        'out_for_delivery': 'in_transit',
        'in_transit': 'in_transit',
        'delivered': 'delivered',
        'buyer_confirmed': 'buyer_confirmed',
        'settled': 'settled',
        'cancelled': 'cancelled',
    }

    ALLOWED_DELIVERY_TRANSITIONS = {
        'pending': {'accepted', 'cancelled'},
        'accepted': {'packed', 'cancelled'},
        'packed': {'out_for_delivery', 'cancelled'},
        'out_for_delivery': {'delivered', 'cancelled'},
        'delivered': set(),
        'cancelled': set(),
    }

    ROLE_DELIVERY_PERMISSIONS = {
        'seller': {'packed', 'handover_pending', 'cancelled'},
        'ops': {'quality_check_pending', 'quality_approved', 'quality_rejected', 'picked_up', 'in_transit', 'delivered', 'settled'},
        'buyer': {'buyer_confirmed'},
    }

    DELIVERY_TRANSITIONS_V2 = {
        'pending': {'order_accepted', 'cancelled'},
        'order_accepted': {'quality_check_pending', 'packed', 'cancelled'},
        'quality_check_pending': {'quality_approved', 'quality_rejected', 'cancelled'},
        'quality_approved': {'packed', 'picked_up', 'cancelled'},
        'quality_rejected': {'cancelled'},
        'packed': {'handover_pending', 'picked_up', 'cancelled'},
        'handover_pending': {'picked_up', 'cancelled'},
        'picked_up': {'in_transit', 'cancelled'},
        'in_transit': {'delivered', 'cancelled'},
        'delivered': {'buyer_confirmed', 'settled'},
        'buyer_confirmed': {'settled'},
        'settled': set(),
        'cancelled': set(),
    }

    def _canonical_delivery_status(self, status: str) -> str:
        return self.CANONICAL_DELIVERY_STATUS_MAP.get(status, status)

    def _legacy_delivery_status(self, status: str) -> str:
        return self.LEGACY_DELIVERY_STATUS_MAP.get(status, status)

    def _delivery_status_label(self, status: str) -> str:
        return self._canonical_delivery_status(status).replace('_', ' ')

    def place_order(self, payload: OrderCreate) -> Order:
        listing = self.store.get_listing(payload.listing_id)
        if listing is None:
            raise ValueError('Listing not found')
        if getattr(listing, 'quality_status', None) == 'rejected':
            raise ValueError('Rejected listings cannot be ordered')
        if payload.quantity_kg > listing.available_kg:
            raise ValueError('Requested quantity exceeds available stock')

        delivery_mode = payload.delivery_mode or 'pickup'
        delivery_address = payload.delivery_address
        delivery_estimate = None
        if delivery_mode == 'delivery' and delivery_address:
            delivery_estimate = self._compute_delivery_estimate(
                listing=listing,
                quantity_kg=payload.quantity_kg,
                delivery_address=delivery_address,
            )
            delivery_address = delivery_estimate.delivery_address

        produce_subtotal = round(payload.quantity_kg * listing.price_per_kg, 2)
        delivery_fee = float(delivery_estimate.total_delivery_fee if delivery_estimate is not None else 0.0)
        buyer_total_payable = round(produce_subtotal + delivery_fee, 2)

        order = Order(
            listing_id=listing.id,
            seller_id=listing.seller_id,
            seller_name=listing.seller_name,
            product_name=listing.product_name,
            buyer_name=payload.buyer_name,
            buyer_phone=payload.phone,
            buyer_type=payload.buyer_type,
            quantity_kg=payload.quantity_kg,
            pickup_time=payload.pickup_time,
            unit_price=listing.price_per_kg,
            total_price=produce_subtotal,
            produce_subtotal=produce_subtotal,
            delivery_mode=delivery_mode,
            delivery_address=delivery_address,
            delivery_distance_km=delivery_estimate.distance_km if delivery_estimate is not None else None,
            delivery_fee=delivery_fee,
            buyer_total_payable=buyer_total_payable,
            delivery_fee_breakdown=(
                self.geo.estimate_delivery_breakdown(
                    quantity_kg=payload.quantity_kg,
                    distance_km=delivery_estimate.distance_km,
                    distance_source=delivery_estimate.distance_source,
                )
                if delivery_estimate is not None
                else None
            ),
            fulfillment_status='pending',
        )
        self.store.save_order(order)

        profile = self.store.get_seller_profile(listing.seller_id)
        quantity = f'{payload.quantity_kg:g}'
        delivery_suffix = ''
        if delivery_estimate is not None:
            distance_display = f'{delivery_estimate.distance_km:g} km' if delivery_estimate.distance_km is not None else 'route pending'
            if profile is not None and profile.preferred_language == 'hi':
                delivery_suffix = (
                    f' माल Rs {produce_subtotal:g} + डिलिवरी Rs {delivery_fee:g}, दूरी लगभग {distance_display}.'
                )
            else:
                delivery_suffix = (
                    f' Produce Rs {produce_subtotal:g} + delivery Rs {delivery_fee:g} for {distance_display}.'
                )
        if profile is not None and profile.preferred_language == 'hi':
            notification_text = (
                f'{payload.quantity_kg} किलो {listing.product_name.lower()} का ऑर्डर {payload.buyer_name} से आया है। '
                f'{delivery_suffix} पिकअप: {payload.pickup_time}। हाँ या नहीं जवाब दें।'
            )
        else:
            notification_text = (
                f'New order: {quantity} kg {listing.product_name} from {payload.buyer_name}. '
                f'{delivery_suffix} Pickup {payload.pickup_time}. Tap Accept or Reject, or reply YES/NO.'
            )
        try:
            whatsapp_result = self.whatsapp.send_reply_buttons(
                to=listing.seller_id,
                body=notification_text,
                buttons=[
                    {'id': f'order_accept:{order.id}', 'title': 'Accept'},
                    {'id': f'order_reject:{order.id}', 'title': 'Reject'},
                ],
            )
            if not whatsapp_result.get('sent'):
                whatsapp_result = self.whatsapp.send_text_message(to=listing.seller_id, body=notification_text)
        except Exception as exc:  # pragma: no cover - network failures depend on runtime
            whatsapp_result = {'sent': False, 'reason': 'send_failed', 'error': str(exc)}

        try:
            audio_base64 = self.speech.synthesize(notification_text)
        except Exception:  # pragma: no cover - cloud TTS failures depend on runtime
            audio_base64 = None

        self.notify_seller(
            recipient_id=listing.seller_id,
            seller_id=listing.seller_id,
            order_id=order.id,
            category='order',
            title='New order',
            text=notification_text,
            entity_type='order',
            entity_id=order.id,
            action_label='Review order',
            action_target='orders',
            channel='whatsapp',
            delivery_status=self.whatsapp.delivery_status(whatsapp_result),
            audio_base64=audio_base64,
        )
        self.notify_buyer(
            recipient_id=payload.phone,
            category='order',
            title='Order placed',
            text=(
                f'Order placed for {listing.product_name}. Produce subtotal Rs {produce_subtotal:g}, '
                f'delivery Rs {delivery_fee:g}, total estimate Rs {buyer_total_payable:g}.'
            ),
            entity_type='order',
            entity_id=order.id,
            action_label='View order',
            action_target='orders',
            seller_id=listing.seller_id,
            order_id=order.id,
        )
        return order

    def respond_to_order(self, order_id: str, decision: str) -> Order:
        order = self.store.get_order(order_id)
        if order is None:
            raise ValueError('Order not found')
        if order.status != 'pending':
            return order

        listing = self.store.get_listing(order.listing_id)
        if listing is None:
            raise ValueError('Listing not found')
        if not order.product_name or order.product_name == 'items':
            order.product_name = listing.product_name

        if decision == 'accept':
            order.status = 'accepted'
            order.fulfillment_status = 'order_accepted'
            listing.available_kg = max(0.0, round(listing.available_kg - order.quantity_kg, 2))
            if listing.available_kg == 0.0:
                listing.status = 'sold_out'

            if order.delivery_mode == 'delivery':
                profile = self.store.get_seller_profile(listing.seller_id)
                seller_lat = profile.latitude if (profile and profile.latitude is not None) else listing.latitude
                seller_lng = profile.longitude if (profile and profile.longitude is not None) else listing.longitude

                buyer_lat = buyer_lng = None
                if order.delivery_address:
                    geocoded = self.geo.geocode(order.delivery_address)
                    if geocoded:
                        buyer_lat = geocoded.get('latitude')
                        buyer_lng = geocoded.get('longitude')

                distance = self.geo.haversine_km(seller_lat, seller_lng, buyer_lat, buyer_lng)
                delivery = Delivery(
                    order_id=order.id,
                    pool_id=order.pool_id,
                    seller_id=order.seller_id,
                    seller_name=order.seller_name,
                    buyer_id=order.buyer_phone,
                    buyer_name=order.buyer_name,
                    product_name=order.product_name,
                    quantity_kg=order.quantity_kg,
                    delivery_mode='delivery',
                    delivery_address=order.delivery_address,
                    latitude=buyer_lat,
                    longitude=buyer_lng,
                    distance_km=distance,
                    delivery_fee=order.delivery_fee,
                    status='order_accepted',
                    current_actor_role='ops' if listing.quality_status == 'pending' else 'seller',
                )
                self.store.save_delivery(delivery)
            self.notify_buyer(
                recipient_id=order.buyer_phone,
                category='order',
                title='Seller accepted order',
                text=f'{order.seller_name} accepted your {order.product_name} order for {order.quantity_kg:g} kg.',
                entity_type='order',
                entity_id=order.id,
                action_label='Track delivery' if order.delivery_mode == 'delivery' else 'View order',
                action_target='orders',
                seller_id=order.seller_id,
                order_id=order.id,
            )
        else:
            order.status = 'rejected'
            order.fulfillment_status = 'cancelled'
            self.notify_buyer(
                recipient_id=order.buyer_phone,
                category='order',
                title='Seller rejected order',
                text=f'{order.seller_name} could not accept your {order.product_name} order.',
                entity_type='order',
                entity_id=order.id,
                action_label='Browse listings',
                action_target='marketplace',
                seller_id=order.seller_id,
                order_id=order.id,
            )

        self.store.save_order(order)
        self.store.save_listing(listing)

        recent_orders = len([
            item for item in self.store.list_orders() if item.seller_id == listing.seller_id and item.status == 'accepted'
        ])
        insight = self.extractor.build_insight(
            seller_id=listing.seller_id,
            seller_name=listing.seller_name,
            product_name=listing.product_name,
            available_kg=listing.available_kg,
            recent_orders=recent_orders,
        )
        self.store.save_insight(insight)
        if decision == 'accept' and order.delivery_mode == 'delivery':
            self.notify_ops(
                category='delivery',
                title='Delivery moved to ops',
                text=f'{order.product_name} order {order.id} needs managed delivery coordination.',
                entity_type='delivery',
                entity_id=order.id,
                action_label='Open deliveries',
                action_target='deliveries',
                seller_id=order.seller_id,
                order_id=order.id,
            )
        return order

    def create_demand_request(self, payload: DemandRequestCreate) -> DemandRequest:
        signals = self.extractor.parse_listing_signals(payload.product_query)
        product_name = signals.get('product_name') or payload.product_query.strip().title()
        category = signals.get('category')
        if category not in {'vegetables', 'fruits', 'grains', 'spices', 'other'}:
            category = 'vegetables'

        lat = lng = None
        place_id = None
        address = payload.delivery_address
        geocoded = self.geo.geocode(payload.delivery_address)
        if geocoded:
            address = geocoded.get('pickup_location') or address
            lat = geocoded.get('latitude')
            lng = geocoded.get('longitude')
            place_id = geocoded.get('place_id')

        locality_key = self._locality_key(product_name, lat, lng, address)

        request = DemandRequest(
            buyer_id=payload.buyer_id,
            buyer_name=payload.buyer_name,
            product_query=payload.product_query,
            product_name=product_name,
            category=category,
            quantity_kg=payload.quantity_kg,
            max_price_per_kg=payload.max_price_per_kg,
            delivery_mode=payload.delivery_mode,
            delivery_address=address,
            latitude=lat,
            longitude=lng,
            place_id=place_id,
            locality_key=locality_key,
            needed_by=payload.needed_by,
            phone=payload.phone,
            status='open',
        )
        self.store.save_demand_request(request)
        self.rebuild_commit_pools(product_name=product_name)
        self.notify_buyer(
            recipient_id=payload.phone,
            category='demand',
            title='Demand request created',
            text=f'Demand request created for {product_name}, {payload.quantity_kg:g} kg at {address}.',
            entity_type='demand',
            entity_id=request.id,
            action_label='View my demands',
            action_target='demand',
        )
        return request

    def _locality_key(self, product_name: str, lat: float | None, lng: float | None, address: str | None) -> str:
        base = product_name.strip().lower()
        if lat is not None and lng is not None:
            d = self.settings.pool_geo_bucket_decimals
            return f'{base}|{round(lat, d)},{round(lng, d)}'
        locality = ' '.join((address or 'unknown').strip().lower().split()[:2])
        return f'{base}|{locality}'

    def rebuild_commit_pools(self, product_name: str | None = None) -> list[CommitDemandPool]:
        since = datetime.utcnow() - timedelta(hours=self.settings.pool_window_hours)
        open_requests = [
            r for r in self.store.list_demand_requests()
            if r.status in {'open', 'pooled'} and r.created_at >= since
        ]
        if product_name:
            target = product_name.strip().lower()
            open_requests = [r for r in open_requests if r.product_name.strip().lower() == target]

        for pool in self.store.list_commit_pools():
            if pool.status in {'open', 'forming'}:
                if not product_name or pool.product_name.strip().lower() == product_name.strip().lower():
                    self.store.delete_commit_pool(pool.id)

        groups: dict[str, list[DemandRequest]] = {}
        for r in open_requests:
            groups.setdefault(r.locality_key, []).append(r)

        built: list[CommitDemandPool] = []
        for locality_key, reqs in groups.items():
            members = [PoolMember(
                request_id=r.id, buyer_id=r.buyer_id, buyer_name=r.buyer_name,
                quantity_kg=r.quantity_kg, delivery_address=r.delivery_address,
                latitude=r.latitude, longitude=r.longitude, max_price_per_kg=r.max_price_per_kg,
            ) for r in reqs]
            lats = [m.latitude for m in members if m.latitude is not None]
            lngs = [m.longitude for m in members if m.longitude is not None]
            prices = [m.max_price_per_kg for m in members if m.max_price_per_kg is not None]
            
            suggested_max = min(prices) if prices else None
            centroid_lat = round(sum(lats) / len(lats), 6) if lats else None
            centroid_lng = round(sum(lngs) / len(lngs), 6) if lngs else None
            
            status = 'open' if len(members) >= self.settings.pool_min_buyers else 'forming'
            pool = CommitDemandPool(
                product_name=reqs[0].product_name,
                category=reqs[0].category,
                locality_key=locality_key,
                locality_label=' '.join(reqs[0].delivery_address.split()[:3]),
                total_quantity_kg=round(sum(m.quantity_kg for m in members), 2),
                buyer_count=len(members),
                suggested_max_price_per_kg=suggested_max,
                centroid_lat=centroid_lat,
                centroid_lng=centroid_lng,
                members=members,
                market_price_reference=self.market_price.get_best_market_reference(
                    reqs[0].product_name,
                    pickup_location=reqs[0].delivery_address,
                ),
                status=status,
            )
            self.store.save_commit_pool(pool)
            for r in reqs:
                r.status = 'pooled'
                r.pool_id = pool.id
                r.updated_at = datetime.utcnow()
                self.store.save_demand_request(r)

            if status == 'open':
                fingerprint = f'pool_open|{pool.id}'
                claim_finger = getattr(self.store, 'claim_demand_alert_fingerprint', None)
                mark_finger = getattr(self.store, 'mark_demand_alert_fingerprint_processed', None)
                if callable(claim_finger) and claim_finger(fingerprint, window_seconds=86400):
                    active_sellers = [p for p in self.list_seller_profiles() if p.registration_status == 'active']
                    alert_body = f'{pool.total_quantity_kg:g} kg {pool.product_name} demand pooled in {pool.locality_label} - open the app to commit.'
                    if pool.market_price_reference is not None and pool.market_price_reference.mandi_modal_price_per_kg is not None:
                        alert_body += (
                            f' Latest mandi modal Rs {pool.market_price_reference.mandi_modal_price_per_kg}/kg.'
                            f' Suggested seller price Rs {pool.market_price_reference.suggested_min_price_per_kg}-Rs {pool.market_price_reference.suggested_max_price_per_kg}/kg.'
                        )
                    for profile in active_sellers:
                        try:
                            whatsapp_res = self.whatsapp.send_text_message(to=profile.seller_id, body=alert_body)
                            self.notify_seller(
                                recipient_id=profile.seller_id,
                                seller_id=profile.seller_id,
                                order_id=f'pool_alert:{pool.id}',
                                category='demand',
                                title='Demand pool open',
                                text=alert_body,
                                entity_type='pool',
                                entity_id=pool.id,
                                action_label='Open demand pools',
                                action_target='demand',
                                channel='whatsapp',
                                delivery_status=self.whatsapp.delivery_status(whatsapp_res),
                            )
                        except Exception:
                            pass
                    if callable(mark_finger):
                        mark_finger(fingerprint)

            built.append(pool)
        return built

    def list_commit_pools(self, seller_id: str | None = None) -> list[CommitDemandPool]:
        pools = [p for p in self.store.list_commit_pools() if p.status in {'open', 'committed', 'fulfilling', 'forming'}]
        if seller_id:
            profile = self.store.get_seller_profile(seller_id)
            if profile and profile.latitude is not None and profile.longitude is not None:
                def keyfn(p):
                    d = self.geo.haversine_km(profile.latitude, profile.longitude, p.centroid_lat, p.centroid_lng)
                    return (d if d is not None else 1e9, -p.total_quantity_kg)
                return sorted(pools, key=keyfn)
        return sorted(pools, key=lambda p: (-p.total_quantity_kg, p.updated_at))

    def commit_to_pool(self, pool_id: str, payload: PoolCommitIn) -> dict:
        pool = self.store.get_commit_pool(pool_id)
        if pool is None:
            raise ValueError('Pool not found')
        if pool.status not in {'open', 'forming'}:
            raise ValueError('Pool is no longer open')

        listing = self.store.get_listing(payload.listing_id)
        if listing is None or listing.seller_id != payload.seller_id:
            raise ValueError('Listing not found for this seller')
        if listing.available_kg < pool.total_quantity_kg:
            raise ValueError('Listing stock is less than the pooled demand')

        price = payload.price_per_kg or listing.price_per_kg
        profile = self.store.get_seller_profile(payload.seller_id)
        seller_lat = profile.latitude if profile else listing.latitude
        seller_lng = profile.longitude if profile else listing.longitude

        created_orders = []
        created_deliveries = []
        for member in pool.members:
            distance = self.geo.haversine_km(seller_lat, seller_lng, member.latitude, member.longitude)
            breakdown = self.geo.estimate_delivery_breakdown(
                quantity_kg=member.quantity_kg,
                distance_km=distance,
                distance_source='haversine' if distance is not None else 'unavailable',
            )
            produce_subtotal = round(member.quantity_kg * price, 2)
            order = Order(
                listing_id=listing.id,
                seller_id=listing.seller_id,
                seller_name=listing.seller_name,
                product_name=listing.product_name,
                buyer_name=member.buyer_name,
                buyer_phone=None,
                buyer_type='kirana',
                quantity_kg=member.quantity_kg,
                pickup_time=pool.locality_label,
                unit_price=price,
                total_price=produce_subtotal,
                produce_subtotal=produce_subtotal,
                status='accepted',
                delivery_mode='delivery',
                delivery_address=member.delivery_address,
                delivery_distance_km=distance,
                delivery_fee=breakdown.total_delivery_fee,
                buyer_total_payable=round(produce_subtotal + breakdown.total_delivery_fee, 2),
                delivery_fee_breakdown=breakdown,
                pool_id=pool.id,
                fulfillment_status='order_accepted',
            )
            self.store.save_order(order)
            created_orders.append(order)

            delivery = Delivery(
                order_id=order.id,
                pool_id=pool.id,
                seller_id=listing.seller_id,
                seller_name=listing.seller_name,
                buyer_id=member.buyer_id,
                buyer_name=member.buyer_name,
                product_name=listing.product_name,
                quantity_kg=member.quantity_kg,
                delivery_mode='delivery',
                delivery_address=member.delivery_address,
                latitude=member.latitude,
                longitude=member.longitude,
                distance_km=distance,
                delivery_fee=breakdown.total_delivery_fee,
                status='order_accepted',
                current_actor_role='ops' if listing.quality_status == 'pending' else 'seller',
            )
            self.store.save_delivery(delivery)
            created_deliveries.append(delivery)
            self.notify_buyer(
                recipient_id=member.buyer_id,
                category='demand',
                title='Seller committed to your demand pool',
                text=(
                    f'{listing.seller_name} committed to your {listing.product_name} demand. '
                    f'Estimated total is Rs {order.buyer_total_payable:g}.'
                ),
                entity_type='order',
                entity_id=order.id,
                action_label='Track delivery',
                action_target='orders',
                seller_id=listing.seller_id,
                order_id=order.id,
            )

            req = self.store.get_demand_request(member.request_id)
            if req:
                req.status = 'committed'
                req.order_id = order.id
                req.updated_at = datetime.utcnow()
                self.store.save_demand_request(req)

        listing.available_kg = max(0.0, round(listing.available_kg - pool.total_quantity_kg, 2))
        if listing.available_kg == 0.0:
            listing.status = 'sold_out'
        self.store.save_listing(listing)

        pool.status = 'committed'
        pool.committed_seller_id = listing.seller_id
        pool.committed_seller_name = listing.seller_name
        pool.committed_price_per_kg = price
        pool.updated_at = datetime.utcnow()
        self.store.save_commit_pool(pool)

        msg = (f'You committed to {pool.total_quantity_kg:g} kg {pool.product_name} '
               f'for {pool.buyer_count} buyers in {pool.locality_label}. '
               f'{len(created_deliveries)} deliveries created.')
        try:
            result = self.whatsapp.send_text_message(to=listing.seller_id, body=msg)
        except Exception as exc:
            result = {'sent': False, 'reason': 'send_failed', 'error': str(exc)}
        
        self.notify_seller(
            recipient_id=listing.seller_id,
            seller_id=listing.seller_id,
            order_id=f'pool_commit:{pool.id}',
            category='demand',
            title='Pool committed',
            text=msg,
            entity_type='pool',
            entity_id=pool.id,
            action_label='Open deliveries',
            action_target='deliveries',
            channel='whatsapp',
            delivery_status=self.whatsapp.delivery_status(result),
        )

        return {'pool': pool, 'orders': created_orders, 'deliveries': created_deliveries}

    def list_deliveries(self, seller_id: str | None = None, buyer_id: str | None = None) -> list[Delivery]:
        items = self.store.list_deliveries()
        if seller_id:
            items = [d for d in items if d.seller_id == seller_id]
        if buyer_id:
            matched: list[Delivery] = []
            for delivery in items:
                if delivery.buyer_id == buyer_id:
                    matched.append(delivery)
                    continue
                if delivery.buyer_id is None:
                    order = self.store.get_order(delivery.order_id)
                    if order and order.buyer_phone == buyer_id:
                        delivery.buyer_id = buyer_id
                        self.store.save_delivery(delivery)
                        matched.append(delivery)
            items = matched
        for delivery in items:
            canonical_status = self._canonical_delivery_status(delivery.status)
            if canonical_status != delivery.status:
                delivery.status = canonical_status
        return sorted(items, key=lambda d: d.created_at, reverse=True)

    def list_buyer_demand_requests(self, buyer_id: str) -> list[DemandRequest]:
        items = [r for r in self.store.list_demand_requests() if r.buyer_id == buyer_id]
        return sorted(items, key=lambda r: r.created_at, reverse=True)

    def list_pending_quality_checks(self) -> list[Listing]:
        items = [listing for listing in self.store.list_listings() if listing.quality_status == 'pending']
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def update_listing_quality(self, listing_id: str, payload: ListingQualityUpdateIn) -> Listing:
        listing = self.store.get_listing(listing_id)
        if listing is None:
            raise ValueError('Listing not found')

        if payload.status == 'approved' and payload.grade is None:
            raise ValueError('Approved quality checks must include a grade')

        next_grade = payload.grade if payload.grade is not None else None
        listing.quality_status = payload.status
        listing.quality_grade = next_grade or listing.quality_grade
        listing.quality_confidence = payload.confidence
        listing.quality_notes = payload.notes
        listing.quality_proof_images = payload.proof_images or listing.quality_proof_images
        listing.verified_by_bolbazaar = payload.status == 'approved'
        listing.quality_checked_at = datetime.utcnow()
        listing.quality_checked_by = payload.checked_by

        if payload.status == 'approved' and next_grade is not None:
            listing.quality_grade = next_grade
            listing.freshness_label = f'BolBazaar Verified Grade {next_grade}'
        elif payload.status == 'rejected':
            listing.freshness_label = 'Quality rejected'
        else:
            listing.freshness_label = 'Quality pending'

        self.store.save_listing(listing)

        for delivery in [item for item in self.store.list_deliveries() if item.order_id in {order.id for order in self.store.list_orders() if order.listing_id == listing.id}]:
            canonical = self._canonical_delivery_status(delivery.status)
            if payload.status == 'approved' and canonical in {'order_accepted', 'quality_check_pending'}:
                delivery.status = 'quality_approved'
                delivery.current_actor_role = 'seller'
            elif payload.status == 'rejected' and canonical != 'cancelled':
                delivery.status = 'quality_rejected'
                delivery.current_actor_role = 'ops'
            delivery.updated_at = datetime.utcnow()
            self.store.save_delivery(delivery)
            order = self.store.get_order(delivery.order_id)
            if order:
                order.fulfillment_status = delivery.status
                if payload.status == 'rejected':
                    order.quality_issue_reported = True
                    order.quality_issue_notes = payload.notes
                self.store.save_order(order)

        seller_text = (
            f'{listing.product_name} quality approved with grade {listing.quality_grade}.'
            if payload.status == 'approved'
            else f'{listing.product_name} quality rejected. {payload.notes or ""}'.strip()
        )
        self.notify_seller(
            recipient_id=listing.seller_id,
            seller_id=listing.seller_id,
            order_id=f'quality:{listing.id}',
            category='quality',
            title='Listing quality updated',
            text=seller_text,
            entity_type='listing',
            entity_id=listing.id,
            action_label='View listing',
            action_target='profile',
        )
        return listing

    def build_ops_metrics(self) -> OpsMetricSnapshot:
        listings = self.store.list_listings()
        deliveries = [delivery for delivery in self.list_deliveries() if delivery.status != 'cancelled']
        orders = self.store.list_orders()
        pools = self.store.list_commit_pools()

        verified_listing_ids = {listing.id for listing in listings if listing.verified_by_bolbazaar and listing.quality_status == 'approved'}
        completed_statuses = {'delivered', 'buyer_confirmed', 'settled'}
        active_statuses = {'order_accepted', 'quality_check_pending', 'quality_approved', 'packed', 'handover_pending', 'picked_up', 'in_transit'}

        return OpsMetricSnapshot(
            total_listings=len(listings),
            verified_listings=len([listing for listing in listings if listing.quality_status == 'approved']),
            pending_quality_checks=len([listing for listing in listings if listing.quality_status == 'pending']),
            rejected_listings=len([listing for listing in listings if listing.quality_status == 'rejected']),
            active_deliveries=len([delivery for delivery in deliveries if delivery.status in active_statuses]),
            completed_deliveries=len([delivery for delivery in deliveries if delivery.status in completed_statuses]),
            demand_pools_matched=len([pool for pool in pools if pool.status in {'committed', 'fulfilling', 'fulfilled'}]),
            estimated_supply_matched_kg=round(sum(order.quantity_kg for order in orders if order.status in {'accepted', 'completed'}), 2),
            orders_fulfilled_through_verified_supply=len([
                order for order in orders
                if order.listing_id in verified_listing_ids and order.status in {'accepted', 'completed'}
            ]),
        )

    def build_ops_dashboard(self) -> OpsDashboardResponse:
        listings = self.store.list_listings()
        active_delivery_statuses = {'order_accepted', 'quality_check_pending', 'quality_approved', 'packed', 'handover_pending', 'picked_up', 'in_transit'}
        return OpsDashboardResponse(
            pending_quality_checks=sorted([listing for listing in listings if listing.quality_status == 'pending'], key=lambda item: item.created_at, reverse=True),
            verified_listings=sorted([listing for listing in listings if listing.quality_status == 'approved'], key=lambda item: item.created_at, reverse=True),
            rejected_listings=sorted([listing for listing in listings if listing.quality_status == 'rejected'], key=lambda item: item.created_at, reverse=True),
            active_deliveries=[delivery for delivery in self.list_deliveries() if delivery.status in active_delivery_statuses],
            metrics=self.build_ops_metrics(),
        )

    def advance_delivery(self, delivery_id: str, next_status: str, *, actor_role: str | None = None, actor_id: str | None = None) -> Delivery:
        delivery = self.store.get_delivery(delivery_id)
        if delivery is None:
            raise ValueError('Delivery not found')
        current_status = self._canonical_delivery_status(delivery.status)
        next_status = self._canonical_delivery_status(next_status)
        allowed = self.DELIVERY_TRANSITIONS_V2.get(current_status, set())
        if next_status not in allowed:
            raise ValueError(f'Cannot move delivery from {current_status} to {next_status}')
        if actor_role is not None:
            permitted = self.ROLE_DELIVERY_PERMISSIONS.get(actor_role, set())
            if next_status not in permitted and next_status != 'cancelled':
                raise ValueError(f'{actor_role} cannot move delivery to {next_status}')

        delivery.status = next_status
        delivery.last_actor_role = actor_role
        delivery.last_actor_id = actor_id
        delivery.current_actor_role = (
            'seller' if next_status in {'quality_approved', 'order_accepted'} else
            'ops' if next_status in {'quality_check_pending', 'packed', 'handover_pending', 'picked_up', 'in_transit'} else
            'buyer' if next_status == 'delivered' else
            None
        )
        if next_status == 'handover_pending':
            delivery.handover_confirmed_at = datetime.utcnow()
        delivery.updated_at = datetime.utcnow()
        self.store.save_delivery(delivery)

        order = self.store.get_order(delivery.order_id)
        if order:
            order.fulfillment_status = next_status
            if next_status in {'buyer_confirmed', 'settled'}:
                order.status = 'completed'
            if next_status == 'quality_rejected':
                order.quality_issue_reported = True
            self.store.save_order(order)

        if next_status in {'buyer_confirmed', 'settled'}:
            req = next((r for r in self.store.list_demand_requests() if r.order_id == delivery.order_id), None)
            if req:
                req.status = 'fulfilled'
                req.updated_at = datetime.utcnow()
                self.store.save_demand_request(req)

            if delivery.pool_id:
                pool = self.store.get_commit_pool(delivery.pool_id)
                if pool:
                    pool_deliveries = [d for d in self.store.list_deliveries() if d.pool_id == pool.id]
                    canonical_pool_statuses = [self._canonical_delivery_status(d.status) for d in pool_deliveries]
                    if canonical_pool_statuses and all(status in {'buyer_confirmed', 'settled'} for status in canonical_pool_statuses):
                        pool.status = 'fulfilled'
                    elif any(status in {'packed', 'handover_pending', 'picked_up', 'in_transit', 'delivered'} for status in canonical_pool_statuses):
                        pool.status = 'fulfilling'
                    pool.updated_at = datetime.utcnow()
                    self.store.save_commit_pool(pool)
        self.notify_seller(
            recipient_id=delivery.seller_id,
            seller_id=delivery.seller_id,
            order_id=delivery.order_id,
            category='delivery',
            title='Delivery status updated',
            text=f'{delivery.product_name} delivery moved to {next_status.replace("_", " ")}.',
            entity_type='delivery',
            entity_id=delivery.id,
            action_label='Open deliveries',
            action_target='deliveries',
        )
        if delivery.buyer_id:
            self.notify_buyer(
                recipient_id=delivery.buyer_id,
                category='delivery',
                title='Delivery status updated',
                text=f'{delivery.product_name} delivery is now {next_status.replace("_", " ")}.',
                entity_type='delivery',
                entity_id=delivery.id,
                action_label='Track delivery',
                action_target='orders',
                seller_id=delivery.seller_id,
                order_id=delivery.order_id,
            )
        return delivery

    def advance_delivery_for_actor(self, delivery_id: str, payload: DeliveryAdvanceRequestIn) -> Delivery:
        delivery = self.store.get_delivery(delivery_id)
        if delivery is None:
            raise ValueError('Delivery not found')
        if payload.actor_role == 'seller':
            if payload.actor_id and payload.actor_id != delivery.seller_id:
                raise ValueError('Seller cannot advance another seller delivery')
        if payload.actor_role == 'buyer':
            if payload.actor_id and delivery.buyer_id and payload.actor_id != delivery.buyer_id:
                raise ValueError('Buyer cannot advance another buyer delivery')
        return self.advance_delivery(
            delivery_id,
            payload.next_status,
            actor_role=payload.actor_role,
            actor_id=payload.actor_id,
        )

    def confirm_buyer_delivery(self, delivery_id: str, payload: BuyerDeliveryConfirmIn) -> Delivery:
        delivery = self.store.get_delivery(delivery_id)
        if delivery is None:
            raise ValueError('Delivery not found')
        if delivery.buyer_id and delivery.buyer_id != payload.buyer_id:
            raise ValueError('Buyer cannot confirm another buyer delivery')
        if self._canonical_delivery_status(delivery.status) not in {'delivered', 'buyer_confirmed'}:
            raise ValueError('Delivery is not ready for buyer confirmation')
        delivery = self.advance_delivery(
            delivery_id,
            'buyer_confirmed',
            actor_role='buyer',
            actor_id=payload.buyer_id,
        )
        order = self.store.get_order(delivery.order_id)
        if order and payload.quality_issue:
            order.quality_issue_reported = True
            order.quality_issue_notes = payload.notes
            self.store.save_order(order)
        return delivery

