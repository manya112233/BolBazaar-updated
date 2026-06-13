from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime
from typing import Any

from app.schemas import DeliveryAdvanceRequestIn, LedgerCaptureMode, LedgerEntry, PricingSuggestionIn, ProduceQualityAssessment, SellerDashboard, SellerProfile, SellerSession
from app.services.geo_service import GeoService
from app.services.marketplace import MarketplaceService
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)
DEFAULT_PICKUP_LOCATION = 'Local pickup'

MENU_ACTION_DASHBOARD = 'menu_dashboard'
MENU_ACTION_ADD_LISTING = 'menu_add_listing'
MENU_ACTION_LISTINGS = 'menu_live_listings'
MENU_ACTION_ORDERS = 'menu_orders'
MENU_ACTION_LEDGER = 'menu_ledger'
MENU_ACTION_DEMAND = 'menu_demand_pools'
MENU_ACTION_CUSTOMERS = 'menu_customers'
MENU_ACTION_PROFILE = 'menu_profile'
MENU_ACTION_VERIFICATION = 'menu_verification_tools'
MENU_ACTION_UPDATE_NAME = 'menu_update_name'
MENU_ACTION_UPDATE_STORE_NAME = 'menu_update_store_name'
MENU_ACTION_CHANGE_LANGUAGE = 'menu_change_language'
MENU_ACTION_UPDATE_SELLER_TYPE = 'menu_update_seller_type'
MENU_ACTION_UPDATE_VERIFICATION_METHOD = 'menu_update_verification_method'
MENU_ACTION_UPDATE_VERIFICATION_NUMBER = 'menu_update_verification_number'
MENU_ACTION_UPDATE_VERIFICATION_PROOF = 'menu_update_verification_proof'
MENU_ACTION_UPDATE_LOCATION = 'menu_update_location'
MENU_ACTION_HELP = 'menu_help'
LISTING_ACTION_CONFIRM_LIVE = 'listing_confirm_live'
LISTING_ACTION_EDIT = 'listing_edit'
FINGERPRINT_WINDOW_SECONDS = 120
RESPONSE_DEDUP_WINDOW_SECONDS = 15
LANGUAGE_PROMPT_DEDUP_WINDOW_SECONDS = 120
LISTING_SESSION_STATES = {
    'awaiting_listing_message',
    'awaiting_listing_product',
    'awaiting_listing_quantity',
    'awaiting_listing_price',
    'awaiting_listing_confirmation',
}

COPY: dict[str, dict[str, str]] = {
    'en': {
        'welcome_language': 'Welcome to BolBazaar. Choose your language to start seller registration.',
        'ask_owner_name': 'Send your name. Buyers will see this as the seller name.',
        'ask_store_name': 'Send your store or farm name.',
        'ask_store_location': 'Send your default pickup location. Example: Shanti Nagar, Delhi',
        'ask_seller_type': 'Choose seller type: Farmer, Aggregator, FPO, or Trader.',
        'ask_verification_method': 'Choose one verification option. Farmer Registry or PM-KISAN works best for farmers. FPO Certificate, eNAM, or FSSAI works well for aggregators.',
        'ask_verification_number': 'Send your registration or certificate number. If you do not have one, reply SKIP.',
        'ask_verification_proof': 'Now send a photo or PDF screenshot of your proof document. Example: Farmer Registry page, PM-KISAN screen, FPO certificate, eNAM or FSSAI proof.',
        'verification_pending': 'Verification submitted. Your profile is marked verified-for-demo and ready to list. In production, this step can be checked against official registries or reviewed manually.',
        'registration_done': 'Registration complete. Your seller profile is active now.',
        'menu_body': 'Open your seller menu for dashboard, listings, khata ledger, profile, and verification tools.',
        'menu_button': 'Open menu',
        'verification_menu_body': 'Open verification tools to update seller type, verification details, or pickup location.',
        'verification_menu_button': 'Open tools',
        'listing_prompt': 'Send your listing like this: Today I have 20 kilo potato, 30 rupees kilo, Shanti Nagar pickup',
        'listing_prompt_short': 'Send the listing message now, or reply CANCEL.',
        'location_prompt': 'Send the new pickup location now.',
        'name_prompt': 'Send the seller name you want buyers to see. Reply CANCEL to keep the current name.',
        'name_updated': 'Your seller name has been updated.',
        'store_name_prompt': 'Send your store or farm name. Reply CANCEL to keep the current name.',
        'store_name_updated': 'Your store or farm name has been updated.',
        'language_prompt': 'Choose your preferred language.',
        'language_updated': 'Your language has been updated.',
        'seller_type_button': 'Choose type',
        'seller_type_updated': 'Your seller type has been updated. If your documents changed too, update your verification details.',
        'verification_method_updated': 'Your verification method has been updated. Update your verification ID or proof too if needed.',
        'verification_number_prompt': 'Send your registration or certificate number. Reply SKIP to clear it or CANCEL to keep the current value.',
        'verification_number_updated': 'Your verification ID has been updated.',
        'verification_proof_prompt': 'Send a new photo or PDF screenshot of your proof document. Reply SKIP to clear the current proof or CANCEL to keep it.',
        'verification_proof_updated': 'Your verification proof has been updated.',
        'help': 'Tip: reply MENU any time. You can also send KHATA, NAME, STORE, LANGUAGE, TYPE, VERIFY METHOD, VERIFY ID, VERIFY PROOF, or LOCATION.',
        'unknown': 'I did not understand that. Reply MENU to open seller options.',
        'location_updated': 'Your store pickup location has been updated.',
        'dashboard_empty': 'No sales yet today. Add a listing to start receiving orders.',
        'ledger_empty': 'No khata records yet. Send a note like: Raju bought 10 kg tomatoes for Rs 250 and still owes Rs 50.',
        'customers_empty': 'No customers yet. Once orders are accepted, customer names will appear here.',
        'orders_empty': 'No orders yet. New buyer orders will appear here.',
        'listings_empty': 'No live listings right now. Use New listing from the menu.',
        'profile_title': 'Your seller profile',
        'duplicate_listing': 'That same listing text was already processed just now, so I skipped the duplicate.',
        'deliveries_empty': 'No active deliveries right now. Delivery tracking will appear here after you accept delivery orders.',
        'delivery_invalid_transition': 'That delivery action is not allowed right now. Reply DELIVERIES to see the next valid step.',
        'delivery_not_found': 'Delivery was not found for this seller. Reply DELIVERIES to see your active deliveries.',
        'delivery_status_title': 'Your active deliveries:',
        'quality_empty': 'No quality-tracked listings yet. Create a listing first and BolBazaar will show its verification state here.',
        'status_title': 'Seller status summary',
    },
    'hi': {
        'welcome_language': 'BolBazaar में आपका स्वागत है। विक्रेता पंजीकरण शुरू करने के लिए भाषा चुनें।',
        'ask_owner_name': 'अपना नाम भेजें। खरीदारों को यही विक्रेता नाम दिखाई देगा।',
        'ask_store_name': 'अपनी दुकान या फार्म का नाम भेजें।',
        'ask_store_location': 'अपना डिफॉल्ट पिकअप स्थान भेजें। उदाहरण: शांति नगर, दिल्ली',
        'ask_seller_type': 'विक्रेता का प्रकार चुनें: किसान, एग्रीगेटर, FPO या ट्रेडर।',
        'ask_verification_method': 'एक सत्यापन विकल्प चुनें। किसानों के लिए Farmer Registry या PM-KISAN बेहतर है। एग्रीगेटर के लिए FPO Certificate, eNAM या FSSAI उपयोगी है।',
        'ask_verification_number': 'अपना पंजीकरण या प्रमाणपत्र नंबर भेजें। अगर नंबर नहीं है, तो SKIP लिखें।',
        'ask_verification_proof': 'अब अपने प्रमाण दस्तावेज का फोटो या PDF स्क्रीनशॉट भेजें। जैसे Farmer Registry पेज, PM-KISAN स्क्रीन, FPO certificate, eNAM या FSSAI proof।',
        'verification_pending': 'सत्यापन जमा हो गया है। डेमो के लिए आपकी प्रोफाइल verified मार्क हो गई है और आप लिस्टिंग कर सकते हैं। प्रोडक्शन में यह चरण आधिकारिक रजिस्ट्रियों या मैनुअल रिव्यू से जांचा जा सकता है।',
        'registration_done': 'पंजीकरण पूरा हो गया है। आपकी विक्रेता प्रोफाइल अब सक्रिय है।',
        'menu_body': 'डैशबोर्ड, लिस्टिंग, खाता लेजर, प्रोफाइल और सत्यापन टूल देखने के लिए विक्रेता मेनू खोलें।',
        'menu_button': 'मेनू खोलें',
        'verification_menu_body': 'विक्रेता प्रकार, सत्यापन जानकारी या पिकअप स्थान अपडेट करने के लिए सत्यापन टूल खोलें।',
        'verification_menu_button': 'टूल खोलें',
        'listing_prompt': 'नई लिस्टिंग इस फॉर्मेट में भेजें: आज 20 किलो आलू है, 30 रुपये किलो, शांति नगर पिकअप',
        'listing_prompt_short': 'अब लिस्टिंग भेजें, या CANCEL लिखें।',
        'location_prompt': 'नया पिकअप स्थान अभी भेजें।',
        'name_prompt': 'खरीदारों को जो विक्रेता नाम दिखाना है, वह भेजें। मौजूदा नाम रखने के लिए CANCEL लिखें।',
        'name_updated': 'आपका विक्रेता नाम अपडेट हो गया है।',
        'store_name_prompt': 'अपनी दुकान या फार्म का नाम भेजें। मौजूदा नाम रखने के लिए CANCEL लिखें।',
        'store_name_updated': 'आपकी दुकान या फार्म का नाम अपडेट हो गया है।',
        'language_prompt': 'अपनी पसंद की भाषा चुनें।',
        'language_updated': 'आपकी भाषा अपडेट हो गई है।',
        'seller_type_button': 'प्रकार चुनें',
        'seller_type_updated': 'आपका विक्रेता प्रकार अपडेट हो गया है। अगर आपके दस्तावेज बदल गए हैं, तो सत्यापन जानकारी भी अपडेट करें।',
        'verification_method_updated': 'आपका सत्यापन तरीका अपडेट हो गया है। जरूरत हो तो सत्यापन ID या प्रमाण भी अपडेट करें।',
        'verification_number_prompt': 'अपना पंजीकरण या प्रमाणपत्र नंबर भेजें। इसे हटाने के लिए SKIP लिखें, मौजूदा नंबर रखने के लिए CANCEL लिखें।',
        'verification_number_updated': 'आपकी सत्यापन ID अपडेट हो गई है।',
        'verification_proof_prompt': 'नया प्रमाण फोटो या PDF स्क्रीनशॉट भेजें। मौजूदा प्रमाण हटाने के लिए SKIP लिखें, रखने के लिए CANCEL लिखें।',
        'verification_proof_updated': 'आपका सत्यापन प्रमाण अपडेट हो गया है।',
        'help': 'सुझाव: कभी भी MENU लिखें। आप KHATA, NAME, STORE, LANGUAGE, TYPE, VERIFY METHOD, VERIFY ID, VERIFY PROOF या LOCATION भी भेज सकते हैं।',
        'unknown': 'समझ नहीं आया। विक्रेता विकल्प खोलने के लिए MENU लिखें।',
        'location_updated': 'आपका स्टोर पिकअप स्थान अपडेट हो गया है।',
        'dashboard_empty': 'आज अभी कोई बिक्री नहीं हुई है। ऑर्डर लेना शुरू करने के लिए नई लिस्टिंग जोड़ें।',
        'ledger_empty': 'अभी कोई खाता रिकॉर्ड नहीं है। ऐसा मैसेज भेजें: राजू ने 10 किलो टमाटर 250 रुपये में लिया, 50 रुपये बाकी हैं।',
        'customers_empty': 'अभी कोई ग्राहक नहीं है। ऑर्डर स्वीकार होते ही ग्राहक सूची यहां दिखेगी।',
        'orders_empty': 'अभी कोई ऑर्डर नहीं है। नए खरीदार ऑर्डर यहां दिखेंगे।',
        'listings_empty': 'अभी कोई लाइव लिस्टिंग नहीं है। मेनू से नई लिस्टिंग चुनें।',
        'profile_title': 'आपकी विक्रेता प्रोफाइल',
        'duplicate_listing': 'यही लिस्टिंग टेक्स्ट अभी प्रोसेस हो चुका था, इसलिए डुप्लिकेट छोड़ दिया गया।',
    },
}

SELLER_TYPE_TITLES = {
    'farmer': 'Farmer',
    'aggregator': 'Aggregator',
    'fpo': 'FPO',
    'trader': 'Trader',
}

VERIFICATION_METHOD_TITLES = {
    'farmer_registry': 'Farmer Registry',
    'pm_kisan': 'PM-KISAN',
    'enam': 'eNAM',
    'fpo_certificate': 'FPO Certificate',
    'fssai': 'FSSAI',
    'govt_id': 'Govt ID',
    'other': 'Other Proof',
}


class SellerFlowService:
    def __init__(self, *, store: Any, marketplace: MarketplaceService, whatsapp: WhatsAppService) -> None:
        self.store = store
        self.marketplace = marketplace
        self.whatsapp = whatsapp
        self.geo = GeoService()

    def handle_message(
        self,
        *,
        seller_id: str,
        profile_name: str,
        message_text: str,
        image_url: str | None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
        interaction_id: str | None = None,
        capture_mode: LedgerCaptureMode = 'text_message',
    ) -> dict[str, Any]:
        profile = self._ensure_profile(seller_id=seller_id, profile_name=profile_name)
        session = self.store.get_seller_session(seller_id)
        action = self._normalize_text(interaction_id or message_text)

        if action in {'restart', 'register'}:
            return self._start_registration(profile)

        if profile.registration_status != 'active':
            if session is not None and session.state == 'awaiting_verification_proof':
                return self._complete_verification_capture(profile=profile, raw_text=message_text, image_url=image_url)
            return self._handle_registration(profile=profile, session=session, action=action, raw_text=message_text)

        if session is not None and session.state == 'awaiting_language_update':
            return self._handle_language_update(profile=profile, action=action)
        if session is not None and session.state == 'awaiting_profile_name_update':
            return self._handle_profile_name_update(profile=profile, raw_text=message_text)
        if session is not None and session.state == 'awaiting_store_name_update':
            return self._handle_store_name_update(profile=profile, raw_text=message_text)
        if session is not None and session.state == 'awaiting_seller_type_update':
            return self._handle_seller_type_update(profile=profile, action=action)
        if session is not None and session.state == 'awaiting_verification_method_update':
            return self._handle_verification_method_update(profile=profile, action=action)
        if session is not None and session.state == 'awaiting_verification_number_update':
            return self._handle_verification_number_update(profile=profile, action=action, raw_text=message_text)
        if session is not None and session.state == 'awaiting_verification_proof_update':
            return self._handle_verification_proof_update(profile=profile, action=action, raw_text=message_text, image_url=image_url)
        if session is not None and session.state == 'awaiting_store_location':
            return self._handle_location_update(profile=profile, raw_text=message_text)
        interrupted = self._handle_listing_session_interrupt(profile=profile, session=session, action=action)
        if interrupted is not None:
            return interrupted
        if session is not None and session.state == 'awaiting_listing_confirmation':
            return self._handle_listing_confirmation(
                profile=profile,
                session=session,
                action=action,
                raw_text=message_text,
            )
        if session is not None and session.state in {
            'awaiting_listing_product',
            'awaiting_listing_quantity',
            'awaiting_listing_price',
        }:
            return self._handle_listing_slot_capture(
                profile=profile,
                session=session,
                raw_text=message_text,
                image_url=image_url,
                quality_assessment=self._resolve_quality_assessment(
                    session=session,
                    raw_text=message_text,
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                ),
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                capture_mode=capture_mode,
            )
        if session is not None and session.state == 'awaiting_listing_message':
            return self._handle_listing_capture(
                profile=profile,
                session=session,
                raw_text=message_text,
                image_url=image_url,
                quality_assessment=self._resolve_quality_assessment(
                    session=session,
                    raw_text=message_text,
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                ),
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                capture_mode=capture_mode,
            )

        order_decision = self._parse_order_decision(action)
        if order_decision is not None:
            decision, order_number, order_id = order_decision
            order_response = self._handle_order_decision(
                profile=profile,
                decision=decision,
                order_number=order_number,
                order_id=order_id,
            )
            if order_response is not None:
                return order_response

        delivery_command = self._parse_delivery_command(action)
        if delivery_command is not None:
            delivery_response = self._handle_delivery_command(
                profile=profile,
                delivery_id=delivery_command[0],
                command=delivery_command[1],
            )
            if delivery_response is not None:
                return delivery_response

        routed_command = self._route_active_command(profile, action)
        if routed_command is not None:
            return routed_command

        price_command_product = self._extract_price_command_product(action)
        if price_command_product:
            return self._send_price_intelligence(profile, price_command_product)

        if self._has_ledger_signal(message_text):
            return self._record_ledger_entry(
                profile=profile,
                message_text=message_text,
                capture_mode=capture_mode,
            )

        if image_url and not message_text.strip() and (session is None or session.state in LISTING_SESSION_STATES):
            return self._prompt_for_photo_listing(
                profile=profile,
                quality_assessment=self._resolve_quality_assessment(
                    session=session,
                    raw_text=message_text,
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                ),
                image_url=image_url,
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
            )

        if self._has_listing_signal(message_text):
            return self._prompt_for_listing_confirmation(
                profile=profile,
                draft_message=message_text,
                quality_assessment=self._resolve_quality_assessment(
                    session=session,
                    raw_text=message_text,
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                ),
                capture_mode=capture_mode,
                draft_image_url=image_url,
            )

        return self._send_main_menu(profile, prefix=self._copy(profile, 'unknown'))

    def _copy(self, profile: SellerProfile, key: str) -> str:
        language = profile.preferred_language if profile.preferred_language in COPY else 'hi'
        if key in COPY[language]:
            return COPY[language][key]
        return COPY['en'][key]

    def _is_hindi(self, profile: SellerProfile) -> bool:
        return profile.preferred_language == 'hi'

    def _ensure_profile(self, *, seller_id: str, profile_name: str) -> SellerProfile:
        profile = self.store.get_seller_profile(seller_id)
        if profile is not None:
            if profile_name and profile.seller_name == 'WhatsApp Seller':
                profile.seller_name = profile_name
                profile.updated_at = datetime.utcnow()
                self.store.save_seller_profile(profile)
            return profile

        profile = SellerProfile(
            seller_id=seller_id,
            seller_name=profile_name or 'WhatsApp Seller',
            source_channel='whatsapp',
        )
        self.store.save_seller_profile(profile)
        return profile

    def _normalize_text(self, value: str | None) -> str:
        if not value:
            return ''
        normalized = value.strip().lower()
        normalized = re.sub(r'[^\w\s\u0900-\u097f:-]', ' ', normalized)
        return re.sub(r'\s+', ' ', normalized).strip()

    def _extract_price_command_product(self, action: str) -> str | None:
        normalized = self._normalize_text(action)
        if not normalized:
            return None
        prefixes = ('price ', 'mandi ', 'bhav ', 'भाव ')
        for prefix in prefixes:
            if normalized.startswith(prefix):
                product = normalized[len(prefix):].strip()
                return product or None
        return None

    def _send_price_intelligence(self, profile: SellerProfile, product_query: str) -> dict[str, Any]:
        try:
            reference = self.marketplace.suggest_price(PricingSuggestionIn(
                product_name=product_query,
                pickup_location=profile.default_pickup_location,
            ))
        except Exception:
            reference = None

        if reference is None or reference.mandi_modal_price_per_kg is None:
            body = (
                f'{product_query.title()} का ताज़ा मंडी भाव अभी उपलब्ध नहीं है। बाद में फिर कोशिश करें।'
                if self._is_hindi(profile)
                else f'Latest mandi pricing for {product_query.title()} is unavailable right now. Please try again later.'
            )
            return self._send_text(profile, body, handled='seller_price_lookup')

        if self._is_hindi(profile):
            body = (
                f'{reference.product_name} का मंडी modal भाव लगभग Rs {reference.mandi_modal_price_per_kg}/किलो है। '
                f'सुझाई गई selling range Rs {reference.suggested_min_price_per_kg}-Rs {reference.suggested_max_price_per_kg}/किलो। '
                f'{reference.explanation}'
            )
        else:
            body = (
                f'{reference.product_name} mandi modal is about Rs {reference.mandi_modal_price_per_kg}/kg. '
                f'Suggested selling range is Rs {reference.suggested_min_price_per_kg}-Rs {reference.suggested_max_price_per_kg}/kg. '
                f'{reference.explanation}'
            )
        return self._send_text(profile, body, handled='seller_price_lookup')

    def _matches_command(self, action: str, *, exact: tuple[str, ...] = (), phrases: tuple[str, ...] = ()) -> bool:
        normalized_action = self._normalize_text(action)
        if not normalized_action:
            return False

        if exact:
            normalized_exact = {self._normalize_text(item) for item in exact if item}
            if normalized_action in normalized_exact:
                return True

        if not phrases:
            return False

        padded_action = f' {normalized_action} '
        for phrase in phrases:
            normalized_phrase = self._normalize_text(phrase)
            if normalized_phrase and f' {normalized_phrase} ' in padded_action:
                return True
        return False

    def _save_session(
        self,
        seller_id: str,
        state: str,
        draft_message: str | None = None,
        quality_assessment: ProduceQualityAssessment | None = None,
        draft_capture_mode: LedgerCaptureMode | None = None,
        draft_image_url: str | None = None,
    ) -> None:
        session_kwargs: dict[str, Any] = {
            'seller_id': seller_id,
            'state': state,
            'draft_message': draft_message,
            'draft_capture_mode': draft_capture_mode,
            'draft_image_url': draft_image_url,
        }
        if quality_assessment is not None:
            session_kwargs.update(
                {
                    'draft_quality_grade': quality_assessment.quality_grade,
                    'draft_quality_score': quality_assessment.quality_score,
                    'draft_quality_summary': quality_assessment.quality_summary,
                    'draft_quality_assessment_source': quality_assessment.quality_assessment_source,
                    'draft_quality_signals': quality_assessment.quality_signals,
                    'draft_detected_product_name': quality_assessment.detected_product_name,
                    'draft_detected_category': quality_assessment.detected_category,
                    'draft_estimated_visible_count': quality_assessment.estimated_visible_count,
                }
            )
        self.store.save_seller_session(SellerSession(**session_kwargs))

    def _clear_session(self, seller_id: str) -> None:
        self.store.clear_seller_session(seller_id)

    def _session_quality_assessment(self, session: SellerSession | None) -> ProduceQualityAssessment | None:
        if session is None:
            return None
        if not any(
            [
                session.draft_quality_grade,
                session.draft_quality_summary,
                session.draft_quality_score is not None,
                session.draft_quality_signals,
                session.draft_detected_product_name,
                session.draft_detected_category,
                session.draft_estimated_visible_count is not None,
            ]
        ):
            return None
        return ProduceQualityAssessment(
            quality_grade=session.draft_quality_grade or 'standard',
            quality_score=session.draft_quality_score,
            quality_summary=session.draft_quality_summary,
            quality_assessment_source=session.draft_quality_assessment_source or 'text_signal',
            quality_signals=session.draft_quality_signals,
            detected_product_name=session.draft_detected_product_name,
            detected_category=session.draft_detected_category,
            estimated_visible_count=session.draft_estimated_visible_count,
        )

    def _listing_image_url(
        self,
        *,
        session: SellerSession | None,
        image_url: str | None,
        image_bytes: bytes | None,
        image_mime_type: str | None,
    ) -> str | None:
        resolver = getattr(self.marketplace, 'listing_image_url', None)
        if callable(resolver):
            resolved = resolver(image_url, image_bytes, image_mime_type)
        else:
            resolved = image_url if image_url and image_url.startswith(('http://', 'https://')) else None
        return resolved or (str(session.draft_image_url) if session and session.draft_image_url else None)

    def _effective_listing_capture_mode(
        self,
        session: SellerSession | None,
        capture_mode: LedgerCaptureMode,
    ) -> LedgerCaptureMode:
        if capture_mode == 'voice_note' or (session is not None and session.draft_capture_mode == 'voice_note'):
            return 'voice_note'
        return 'text_message'

    def _quality_product_hint(self, raw_text: str, session: SellerSession | None) -> str | None:
        combined = ' '.join(part for part in [session.draft_message if session else None, raw_text] if part).strip()
        if not combined:
            return None
        signals = self._listing_signals(combined)
        product_name = signals.get('product_name')
        return str(product_name) if product_name else None

    def _resolve_quality_assessment(
        self,
        *,
        session: SellerSession | None,
        raw_text: str,
        image_bytes: bytes | None,
        image_mime_type: str | None,
    ) -> ProduceQualityAssessment | None:
        if image_bytes and image_mime_type:
            assessment = self.marketplace.assess_produce_image(
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                product_hint=self._quality_product_hint(raw_text, session),
            )
            if assessment is not None:
                return assessment
        return self._session_quality_assessment(session)

    def _format_quality_assessment(self, profile: SellerProfile, assessment: ProduceQualityAssessment | None) -> str:
        if assessment is None:
            return (
                'Photo received. AI product detection is not available right now. Send product, kg, price, and pickup.'
                if not self._is_hindi(profile)
                else 'फोटो मिल गया। AI product detection अभी उपलब्ध नहीं है। Product, kilo, price और pickup भेजें।'
            )

        grade = assessment.quality_grade.title()
        score_text = f' ({assessment.quality_score}/100)' if assessment.quality_score is not None else ''
        product_text = f' I detected {assessment.detected_product_name}.' if assessment.detected_product_name else ''
        count_text = (
            f' Around {assessment.estimated_visible_count:g} visible pieces; send kg separately.'
            if assessment.estimated_visible_count is not None
            else ''
        )
        if self._is_hindi(profile):
            return f'फोटो मिल गया।{product_text} AI विजुअल चेक: {grade}{score_text}.{count_text}'
        summary = f' {assessment.quality_summary}' if assessment.quality_summary else ''
        return f'Photo received.{product_text} AI visual check: {grade}{score_text}.{summary}{count_text}'.strip()

    def _prompt_for_photo_listing(
        self,
        *,
        profile: SellerProfile,
        quality_assessment: ProduceQualityAssessment | None,
        image_url: str | None = None,
        image_bytes: bytes | None = None,
        image_mime_type: str | None = None,
    ) -> dict[str, Any]:
        self._save_session(
            profile.seller_id,
            'awaiting_listing_message',
            quality_assessment=quality_assessment,
            draft_image_url=self._listing_image_url(
                session=None,
                image_url=image_url,
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
            ),
        )
        listing_prompt = (
            'Send kg and price like this: 20 kilo, 30 rupees kilo. Add pickup only if different.'
            if quality_assessment and quality_assessment.detected_product_name
            else self._copy(profile, 'listing_prompt')
        )
        body = (
            f'{self._format_quality_assessment(profile, quality_assessment)}\n'
            f'{listing_prompt}\n'
            f'{self._copy(profile, "listing_prompt_short")}'
        )
        return self._send_text(profile, body, handled='seller_listing_prompt')

    def _send_language_prompt(self, profile: SellerProfile) -> dict[str, Any]:
        self._save_session(profile.seller_id, 'awaiting_language')
        result = self.whatsapp.send_reply_buttons(
            to=profile.seller_id,
            body=self._copy(profile, 'welcome_language'),
            buttons=[
                {'id': 'lang_hi', 'title': 'हिंदी'},
                {'id': 'lang_en', 'title': 'English'},
            ],
        )
        if not result.get('sent'):
            fallback = (
                'à¤­à¤¾à¤·à¤¾ à¤šà¥à¤¨à¥‡à¤‚: HINDI à¤¯à¤¾ ENGLISH'
                if profile.preferred_language == 'hi'
                else 'Choose your language: HINDI or ENGLISH'
            )
            self.whatsapp.send_text_message(to=profile.seller_id, body=fallback)
        return {'ok': True, 'handled': 'seller_onboarding_language'}

    def _start_registration(self, profile: SellerProfile) -> dict[str, Any]:
        profile.store_name = None
        profile.seller_type = None
        profile.default_pickup_location = None
        profile.latitude = None
        profile.longitude = None
        profile.place_id = None
        profile.registration_status = 'pending'
        profile.verification_status = 'unverified'
        profile.verification_method = None
        profile.verification_number = None
        profile.verification_proof_url = None
        profile.verification_notes = None
        profile.updated_at = datetime.utcnow()
        self.store.save_seller_profile(profile)
        return self._send_language_prompt(profile)

    def _parse_language(self, action: str) -> str | None:
        if action in {'lang_hi', 'hindi', 'हिंदी', 'हिन्दी'}:
            return 'hi'
        if action in {'lang_en', 'english', 'en', 'अंग्रेजी', 'अंग्रेज़ी'}:
            return 'en'
        return None

    def _handle_registration(
        self,
        *,
        profile: SellerProfile,
        session: SellerSession | None,
        action: str,
        raw_text: str,
    ) -> dict[str, Any]:
        if session is None:
            session = self._recover_registration_session(profile)
            if session is None:
                return self._start_registration(profile)

        if session.state == 'awaiting_language':
            language = self._parse_language(action)
            if language is None:
                recovered_session = self._recover_registration_session(profile)
                if recovered_session is not None and recovered_session.state != 'awaiting_language':
                    return self._handle_registration(
                        profile=profile,
                        session=recovered_session,
                        action=action,
                        raw_text=raw_text,
                    )
                return self._send_language_prompt(profile)
            profile.preferred_language = language  # type: ignore[assignment]
            profile.updated_at = datetime.utcnow()
            self.store.save_seller_profile(profile)
            self._save_session(profile.seller_id, 'awaiting_owner_name')
            return self._send_text(profile, self._copy(profile, 'ask_owner_name'), handled='seller_onboarding_owner')

        if self._is_registration_restart_request(action):
            return self._start_registration(profile)

        if self._is_registration_help_request(action):
            return self._repeat_registration_prompt(profile=profile, session=session)

        cleaned = raw_text.strip()
        if not cleaned:
            return self._send_text(profile, self._copy(profile, 'unknown'), handled='seller_onboarding_retry')

        if session.state == 'awaiting_owner_name':
            profile.seller_name = cleaned
            profile.updated_at = datetime.utcnow()
            self.store.save_seller_profile(profile)
            self._save_session(profile.seller_id, 'awaiting_store_name')
            return self._send_text(profile, self._copy(profile, 'ask_store_name'), handled='seller_onboarding_store')

        if session.state == 'awaiting_store_name':
            profile.store_name = cleaned
            profile.updated_at = datetime.utcnow()
            self.store.save_seller_profile(profile)
            self._save_session(profile.seller_id, 'awaiting_store_location')
            return self._send_text(profile, self._copy(profile, 'ask_store_location'), handled='seller_onboarding_location')

        if session.state == 'awaiting_store_location':
            return self._complete_location_capture(profile=profile, raw_text=cleaned, handled='seller_onboarding_location_done')

        if session.state == 'awaiting_seller_type':
            seller_type = self._parse_seller_type(action)
            if seller_type is None:
                return self._prompt_for_seller_type(profile)
            profile.seller_type = seller_type
            profile.registration_status = 'verification_pending'
            profile.updated_at = datetime.utcnow()
            self.store.save_seller_profile(profile)
            return self._prompt_for_verification_method(profile)

        if session.state == 'awaiting_verification_method':
            verification_method = self._parse_verification_method(action)
            if verification_method is None:
                return self._prompt_for_verification_method(profile)
            profile.verification_method = verification_method
            profile.updated_at = datetime.utcnow()
            self.store.save_seller_profile(profile)
            self._save_session(profile.seller_id, 'awaiting_verification_number')
            return self._send_text(profile, self._copy(profile, 'ask_verification_number'), handled='seller_verification_number')

        if session.state == 'awaiting_verification_number':
            profile.verification_number = None if action == 'skip' else cleaned
            profile.updated_at = datetime.utcnow()
            self.store.save_seller_profile(profile)
            self._save_session(profile.seller_id, 'awaiting_verification_proof')
            return self._send_text(profile, self._copy(profile, 'ask_verification_proof'), handled='seller_verification_proof')

        if session.state == 'awaiting_verification_proof':
            return self._complete_verification_capture(profile=profile, raw_text=cleaned, image_url=None)

        return self._start_registration(profile)

    def _recover_registration_session(self, profile: SellerProfile) -> SellerSession | None:
        state: str | None = None
        if profile.seller_type is not None and profile.verification_method is not None:
            state = 'awaiting_verification_number' if profile.verification_number is None else 'awaiting_verification_proof'
        elif profile.seller_type is not None:
            state = 'awaiting_verification_method'
        elif profile.default_pickup_location:
            state = 'awaiting_seller_type'
        elif profile.store_name:
            state = 'awaiting_store_location'

        if state is None:
            return None

        self._save_session(profile.seller_id, state)
        return self.store.get_seller_session(profile.seller_id)

    def _is_registration_restart_request(self, action: str) -> bool:
        return self._is_menu_request(action) or action in {'restart', 'register'}

    def _is_registration_help_request(self, action: str) -> bool:
        return action in {'help', MENU_ACTION_HELP}

    def _repeat_registration_prompt(self, *, profile: SellerProfile, session: SellerSession) -> dict[str, Any]:
        if session.state == 'awaiting_owner_name':
            return self._send_text(profile, self._copy(profile, 'ask_owner_name'), handled='seller_onboarding_owner')
        if session.state == 'awaiting_store_name':
            return self._send_text(profile, self._copy(profile, 'ask_store_name'), handled='seller_onboarding_store')
        if session.state == 'awaiting_store_location':
            return self._send_text(profile, self._copy(profile, 'ask_store_location'), handled='seller_onboarding_location')
        if session.state == 'awaiting_seller_type':
            return self._prompt_for_seller_type(profile)
        if session.state == 'awaiting_verification_method':
            return self._prompt_for_verification_method(profile)
        if session.state == 'awaiting_verification_number':
            return self._send_text(profile, self._copy(profile, 'ask_verification_number'), handled='seller_verification_number')
        if session.state == 'awaiting_verification_proof':
            return self._send_text(profile, self._copy(profile, 'ask_verification_proof'), handled='seller_verification_proof')
        return self._start_registration(profile)

    def _complete_location_capture(self, *, profile: SellerProfile, raw_text: str, handled: str) -> dict[str, Any]:
        location = raw_text.strip()
        geocoded = self.geo.geocode(location)
        profile.default_pickup_location = geocoded['pickup_location'] if geocoded else location
        profile.latitude = geocoded.get('latitude') if geocoded else None
        profile.longitude = geocoded.get('longitude') if geocoded else None
        profile.place_id = geocoded.get('place_id') if geocoded else None
        profile.registration_status = 'verification_pending'
        profile.updated_at = datetime.utcnow()
        self.store.save_seller_profile(profile)
        return self._prompt_for_seller_type(profile)

    def _prompt_for_seller_type(self, profile: SellerProfile) -> dict[str, Any]:
        return self._send_seller_type_prompt(
            profile,
            state='awaiting_seller_type',
            handled='seller_type_prompt',
        )

    def _parse_seller_type(self, action: str) -> str | None:
        mapping = {
            'seller_farmer': 'farmer',
            'farmer': 'farmer',
            'किसान': 'farmer',
            'seller_aggregator': 'aggregator',
            'aggregator': 'aggregator',
            'एग्रीगेटर': 'aggregator',
            'seller_fpo': 'fpo',
            'fpo': 'fpo',
            'seller_trader': 'trader',
            'trader': 'trader',
            'ट्रेडर': 'trader',
            'व्यापारी': 'trader',
        }
        return mapping.get(action)

    def _prompt_for_verification_method(self, profile: SellerProfile) -> dict[str, Any]:
        return self._send_verification_method_prompt(
            profile,
            state='awaiting_verification_method',
            handled='seller_verification_method_prompt',
        )

    def _send_verification_method_prompt(self, profile: SellerProfile, *, state: str, handled: str) -> dict[str, Any]:
        self._save_session(profile.seller_id, state)
        seller_type = profile.seller_type or 'farmer'
        if seller_type == 'farmer':
            if self._is_hindi(profile):
                buttons = [
                    {'id': 'verify_farmer_registry', 'title': 'किसान रजिस्ट्री'},
                    {'id': 'verify_pm_kisan', 'title': 'PM-KISAN'},
                    {'id': 'verify_govt_id', 'title': 'सरकारी ID'},
                ]
            else:
                buttons = [
                    {'id': 'verify_farmer_registry', 'title': 'Farmer Registry'},
                    {'id': 'verify_pm_kisan', 'title': 'PM-KISAN'},
                    {'id': 'verify_govt_id', 'title': 'Govt ID'},
                ]
        else:
            if self._is_hindi(profile):
                buttons = [
                    {'id': 'verify_fpo_certificate', 'title': 'FPO प्रमाणपत्र'},
                    {'id': 'verify_enam', 'title': 'eNAM'},
                    {'id': 'verify_fssai', 'title': 'FSSAI'},
                ]
            else:
                buttons = [
                    {'id': 'verify_fpo_certificate', 'title': 'FPO Certificate'},
                    {'id': 'verify_enam', 'title': 'eNAM'},
                    {'id': 'verify_fssai', 'title': 'FSSAI'},
                ]
        result = self.whatsapp.send_reply_buttons(
            to=profile.seller_id,
            body=self._copy(profile, 'ask_verification_method'),
            buttons=buttons,
        )
        return {'ok': True, 'handled': handled}

    def _parse_verification_method(self, action: str) -> str | None:
        mapping = {
            'verify_farmer_registry': 'farmer_registry',
            'farmer registry': 'farmer_registry',
            'farmer_registry': 'farmer_registry',
            'किसान रजिस्ट्री': 'farmer_registry',
            'verify_pm_kisan': 'pm_kisan',
            'pm-kisan': 'pm_kisan',
            'pm kisan': 'pm_kisan',
            'pm_kisan': 'pm_kisan',
            'verify_enam': 'enam',
            'enam': 'enam',
            'e-nam': 'enam',
            'verify_fpo_certificate': 'fpo_certificate',
            'fpo certificate': 'fpo_certificate',
            'fpo_certificate': 'fpo_certificate',
            'fpo प्रमाणपत्र': 'fpo_certificate',
            'verify_fssai': 'fssai',
            'fssai': 'fssai',
            'verify_govt_id': 'govt_id',
            'govt id': 'govt_id',
            'government id': 'govt_id',
            'govt_id': 'govt_id',
            'सरकारी id': 'govt_id',
        }
        return mapping.get(action)

    def _verification_method_label(self, profile: SellerProfile, method: str | None = None) -> str:
        selected_method = method or profile.verification_method or ''
        if self._is_hindi(profile):
            return {
                'farmer_registry': 'किसान रजिस्ट्री',
                'pm_kisan': 'PM-KISAN',
                'enam': 'eNAM',
                'fpo_certificate': 'FPO प्रमाणपत्र',
                'fssai': 'FSSAI',
                'govt_id': 'सरकारी ID',
                'other': 'अन्य प्रमाण',
            }.get(selected_method, 'सत्यापन')
        return VERIFICATION_METHOD_TITLES.get(selected_method, 'verification')

    def _verification_number_prompt(self, profile: SellerProfile) -> str:
        method_label = self._verification_method_label(profile)
        if self._is_hindi(profile):
            return (
                f'अपना {method_label} पंजीकरण या प्रमाणपत्र नंबर भेजें। '
                'इसे हटाने के लिए SKIP लिखें, मौजूदा नंबर रखने के लिए CANCEL लिखें।'
            )
        return (
            f'Send your {method_label} registration or certificate number. '
            'Reply SKIP to clear it or CANCEL to keep the current value.'
        )

    def _complete_verification_capture(self, *, profile: SellerProfile, raw_text: str, image_url: str | None) -> dict[str, Any]:
        proof_value = (image_url or raw_text or '').strip()
        if not proof_value or self._normalize_text(proof_value) in {'skip', 'no', 'none'}:
            return self._send_text(profile, self._copy(profile, 'ask_verification_proof'), handled='seller_verification_proof_retry')
        profile.verification_proof_url = image_url or proof_value
        profile.verification_status = 'verified' if image_url else 'manual_review'
        profile.verification_notes = 'Demo verification captured through WhatsApp onboarding'
        profile.registration_status = 'active'
        profile.updated_at = datetime.utcnow()
        self.store.save_seller_profile(profile)
        self._clear_session(profile.seller_id)
        self.whatsapp.send_text_message(to=profile.seller_id, body=self._copy(profile, 'verification_pending'))
        self.whatsapp.send_text_message(to=profile.seller_id, body=self._copy(profile, 'registration_done'))
        self._send_main_menu(profile)
        return {'ok': True, 'handled': 'seller_verification_complete'}

    def _send_text(self, profile: SellerProfile, body: str, *, handled: str) -> dict[str, Any]:
        self.whatsapp.send_text_message(to=profile.seller_id, body=body)
        return {'ok': True, 'handled': handled}

    def _send_main_menu(self, profile: SellerProfile, prefix: str | None = None, *, force_text_fallback: bool = False) -> dict[str, Any]:
        if not self._claim_response_fingerprint(
            profile.seller_id,
            f'menu|{profile.preferred_language}|{prefix or ""}',
            window_seconds=RESPONSE_DEDUP_WINDOW_SECONDS,
        ):
            return {'ok': True, 'ignored': True, 'reason': 'duplicate_menu_response'}
        menu_body = self._copy(profile, 'menu_body')
        if prefix:
            menu_body = f'{prefix}\n\n{menu_body}'
        fallback_commands = (
            'à¤œà¤µà¤¾à¤¬ à¤¦à¥‡à¤‚: DASHBOARD, NEW, LISTINGS, ORDERS, KHATA, CUSTOMERS, PROFILE, NAME, STORE, LANGUAGE, VERIFY, HELP'
            if self._is_hindi(profile)
            else 'Reply with: DASHBOARD, NEW, LISTINGS, ORDERS, KHATA, DEMAND, CUSTOMERS, PROFILE, NAME, STORE, LANGUAGE, VERIFY, HELP'
        )
        fallback = f'{menu_body}\n\n{fallback_commands}'

        if self._is_hindi(profile):
            sections = [
                {
                    'title': 'ओवरव्यू',
                    'rows': [
                        {'id': MENU_ACTION_DASHBOARD, 'title': 'डैशबोर्ड', 'description': 'बिक्री, लिस्टिंग और ऑर्डर'},
                        {'id': MENU_ACTION_ADD_LISTING, 'title': 'नई लिस्टिंग', 'description': 'नया स्टॉक जोड़ें'},
                        {'id': MENU_ACTION_LISTINGS, 'title': 'मेरी लिस्टिंग', 'description': 'लाइव स्टॉक देखें'},
                        {'id': MENU_ACTION_ORDERS, 'title': 'मेरे ऑर्डर', 'description': 'नए और पुराने ऑर्डर देखें'},
                        {'id': MENU_ACTION_LEDGER, 'title': 'खाता', 'description': 'उधार और भुगतान रिकॉर्ड'},
                        {'id': MENU_ACTION_DEMAND, 'title': 'मांग पूल', 'description': 'जुड़ी हुई buyer demand देखें'},
                    ],
                },
                {
                    'title': 'प्रोफाइल',
                    'rows': [
                        {'id': MENU_ACTION_PROFILE, 'title': 'मेरी प्रोफाइल', 'description': 'स्टोर जानकारी और भाषा'},
                        {'id': MENU_ACTION_UPDATE_NAME, 'title': 'नाम अपडेट करें', 'description': 'विक्रेता नाम बदलें'},
                        {'id': MENU_ACTION_UPDATE_STORE_NAME, 'title': 'स्टोर अपडेट करें', 'description': 'दुकान या फार्म नाम बदलें'},
                        {'id': MENU_ACTION_CHANGE_LANGUAGE, 'title': 'भाषा बदलें', 'description': 'हिंदी या अंग्रेजी चुनें'},
                    ],
                },
                {
                    'title': 'टूल',
                    'rows': [
                        {'id': MENU_ACTION_VERIFICATION, 'title': 'सत्यापन टूल', 'description': 'प्रकार, ID, प्रमाण और पिकअप'},
                    ],
                },
            ]
        else:
            sections = [
                {
                    'title': 'Overview',
                    'rows': [
                        {'id': MENU_ACTION_DASHBOARD, 'title': 'Dashboard', 'description': 'Sales, listings, and orders'},
                        {'id': MENU_ACTION_ADD_LISTING, 'title': 'New listing', 'description': 'Create a new stock listing'},
                        {'id': MENU_ACTION_LISTINGS, 'title': 'My listings', 'description': 'See live stock'},
                        {'id': MENU_ACTION_ORDERS, 'title': 'Orders', 'description': 'Review buyer orders'},
                        {'id': MENU_ACTION_LEDGER, 'title': 'Khata ledger', 'description': 'Credit and payment records'},
                        {'id': MENU_ACTION_DEMAND, 'title': 'Demand pools', 'description': 'See pooled buyer demand'},
                    ],
                },
                {
                    'title': 'Profile',
                    'rows': [
                        {'id': MENU_ACTION_PROFILE, 'title': 'My profile', 'description': 'Store details and language'},
                        {'id': MENU_ACTION_UPDATE_NAME, 'title': 'Update name', 'description': 'Change seller display name'},
                        {'id': MENU_ACTION_UPDATE_STORE_NAME, 'title': 'Update store', 'description': 'Change store or farm name'},
                        {'id': MENU_ACTION_CHANGE_LANGUAGE, 'title': 'Change language', 'description': 'Switch Hindi or English'},
                    ],
                },
                {
                    'title': 'Tools',
                    'rows': [
                        {'id': MENU_ACTION_VERIFICATION, 'title': 'Verification tools', 'description': 'Type, ID, proof, and pickup'},
                    ],
                },
            ]
        result = self.whatsapp.send_list_message(
            to=profile.seller_id,
            body=menu_body,
            button_text=self._copy(profile, 'menu_button'),
            sections=sections,
        )
        if force_text_fallback or not result.get('sent'):
            fallback_commands = (
                'जवाब दें: DASHBOARD, NEW, LISTINGS, ORDERS, KHATA, DEMAND, CUSTOMERS, PROFILE, NAME, STORE, LANGUAGE, VERIFY, HELP'
                if self._is_hindi(profile)
                else 'Reply with: DASHBOARD, NEW, LISTINGS, ORDERS, KHATA, DEMAND, CUSTOMERS, PROFILE, NAME, STORE, LANGUAGE, VERIFY, HELP'
            )
            fallback = f'{menu_body}\n\n{fallback_commands}'
            self.whatsapp.send_text_message(to=profile.seller_id, body=fallback)
        return {'ok': True, 'handled': 'seller_menu'}

    def _send_verification_menu(self, profile: SellerProfile) -> dict[str, Any]:
        if self._is_hindi(profile):
            sections = [
                {
                    'title': 'सत्यापन',
                    'rows': [
                        {'id': MENU_ACTION_UPDATE_SELLER_TYPE, 'title': 'विक्रेता प्रकार', 'description': 'किसान, FPO या ट्रेडर बदलें'},
                        {'id': MENU_ACTION_UPDATE_VERIFICATION_METHOD, 'title': 'सत्यापन तरीका', 'description': 'रजिस्ट्री या प्रमाणपत्र प्रकार बदलें'},
                        {'id': MENU_ACTION_UPDATE_VERIFICATION_NUMBER, 'title': 'सत्यापन ID', 'description': 'पंजीकरण नंबर अपडेट करें'},
                        {'id': MENU_ACTION_UPDATE_VERIFICATION_PROOF, 'title': 'सत्यापन प्रमाण', 'description': 'नया दस्तावेज प्रमाण अपलोड करें'},
                    ],
                },
                {
                    'title': 'प्रोफाइल',
                    'rows': [
                        {'id': MENU_ACTION_UPDATE_LOCATION, 'title': 'स्थान अपडेट करें', 'description': 'डिफॉल्ट पिकअप बदलें'},
                        {'id': 'menu', 'title': 'मुख्य मेनू', 'description': 'विक्रेता मेनू पर वापस जाएं'},
                    ],
                },
            ]
        else:
            sections = [
                {
                    'title': 'Verification',
                    'rows': [
                        {'id': MENU_ACTION_UPDATE_SELLER_TYPE, 'title': 'Seller type', 'description': 'Change farmer, FPO, or trader'},
                        {'id': MENU_ACTION_UPDATE_VERIFICATION_METHOD, 'title': 'Verify method', 'description': 'Change registry or certificate type'},
                        {'id': MENU_ACTION_UPDATE_VERIFICATION_NUMBER, 'title': 'Verify ID', 'description': 'Update registration number'},
                        {'id': MENU_ACTION_UPDATE_VERIFICATION_PROOF, 'title': 'Verify proof', 'description': 'Upload a document proof'},
                    ],
                },
                {
                    'title': 'Profile',
                    'rows': [
                        {'id': MENU_ACTION_UPDATE_LOCATION, 'title': 'Update location', 'description': 'Change default pickup'},
                        {'id': 'menu', 'title': 'Main menu', 'description': 'Back to seller menu'},
                    ],
                },
            ]
        result = self.whatsapp.send_list_message(
            to=profile.seller_id,
            body=self._copy(profile, 'verification_menu_body'),
            button_text=self._copy(profile, 'verification_menu_button'),
            sections=sections,
        )
        if not result.get('sent'):
            fallback_commands = (
                'जवाब दें: TYPE, VERIFY METHOD, VERIFY ID, VERIFY PROOF, LOCATION, MENU'
                if self._is_hindi(profile)
                else 'Reply with: TYPE, VERIFY METHOD, VERIFY ID, VERIFY PROOF, LOCATION, MENU'
            )
            fallback = f"{self._copy(profile, 'verification_menu_body')}\n\n{fallback_commands}"
            self.whatsapp.send_text_message(to=profile.seller_id, body=fallback)
        return {'ok': True, 'handled': 'seller_verification_menu'}

    def _is_menu_request(self, action: str) -> bool:
        return action in {'menu', 'start', 'hello', 'hi', 'bolbazaar', 'मेनू', 'शुरू', 'नमस्ते'}

    def _is_greeting_request(self, action: str) -> bool:
        return re.match(r'^(hi|hello|hey|namaste)\b', action) is not None

    def _is_verification_menu_request(self, action: str) -> bool:
        return action in {MENU_ACTION_VERIFICATION, 'verify', 'verification', 'verification tools'}

    def _is_dashboard_request(self, action: str) -> bool:
        return action in {MENU_ACTION_DASHBOARD, 'dashboard', 'stats', 'overview'}

    def _is_add_listing_request(self, action: str) -> bool:
        return action in {MENU_ACTION_ADD_LISTING, 'new', 'new listing', 'add listing', 'listing'}

    def _is_listings_request(self, action: str) -> bool:
        return action in {MENU_ACTION_LISTINGS, 'listings', 'my listings', 'stock'}

    def _is_orders_request(self, action: str) -> bool:
        return action in {MENU_ACTION_ORDERS, 'orders', 'my orders'}

    def _is_ledger_request(self, action: str) -> bool:
        return action in {MENU_ACTION_LEDGER, 'khata', 'ledger', 'bahi', 'baki', 'balance', 'dues'}

    def _is_customers_request(self, action: str) -> bool:
        return action in {MENU_ACTION_CUSTOMERS, 'customers', 'buyers'}

    def _is_profile_request(self, action: str) -> bool:
        return action in {MENU_ACTION_PROFILE, 'profile'}

    def _is_update_name_request(self, action: str) -> bool:
        return action in {MENU_ACTION_UPDATE_NAME, 'name', 'update name', 'change name'}

    def _is_update_store_name_request(self, action: str) -> bool:
        return action in {MENU_ACTION_UPDATE_STORE_NAME, 'store', 'store name', 'farm name', 'update store', 'update store name'}

    def _is_change_language_request(self, action: str) -> bool:
        return action in {
            MENU_ACTION_CHANGE_LANGUAGE,
            'language',
            'change language',
            'update language',
            'bhasha',
            'भाषा',
            'भाषा बदलें',
        }

    def _is_update_seller_type_request(self, action: str) -> bool:
        return action in {MENU_ACTION_UPDATE_SELLER_TYPE, 'type', 'seller type', 'update type', 'update seller type'}

    def _is_update_verification_method_request(self, action: str) -> bool:
        return action in {MENU_ACTION_UPDATE_VERIFICATION_METHOD, 'verify method', 'verification method', 'update verification method'}

    def _is_update_verification_number_request(self, action: str) -> bool:
        return action in {
            MENU_ACTION_UPDATE_VERIFICATION_NUMBER,
            'verify id',
            'verification id',
            'verify number',
            'verification number',
            'update verification id',
        }

    def _is_update_verification_proof_request(self, action: str) -> bool:
        return action in {
            MENU_ACTION_UPDATE_VERIFICATION_PROOF,
            'verify proof',
            'verification proof',
            'update verification proof',
            'update proof',
        }

    def _is_update_location_request(self, action: str) -> bool:
        return action in {MENU_ACTION_UPDATE_LOCATION, 'location', 'update location'}

    def _is_help_request(self, action: str) -> bool:
        return action in {MENU_ACTION_HELP, 'help'}

    def _is_menu_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(
                'menu',
                'start',
                'hello',
                'hi',
                'bolbazaar',
                'namaste',
                '\u092e\u0947\u0928\u0942',
                '\u0936\u0941\u0930\u0942',
                '\u0928\u092e\u0938\u094d\u0924\u0947',
            ),
            phrases=(
                'open menu',
                'show menu',
                'seller menu',
                'main menu',
                'menu open',
                'menu kholo',
                'menu khol do',
                'menu dikhao',
                'menu dikhaiye',
                'seller options',
                'show seller options',
                'open seller options',
                'open seller menu',
                'show seller menu',
                'bol bazaar menu',
                '\u092e\u0947\u0928\u0942 \u0916\u094b\u0932\u094b',
                '\u092e\u0947\u0928\u0942 \u0926\u093f\u0916\u093e\u0913',
                '\u092e\u0941\u0916\u094d\u092f \u092e\u0947\u0928\u0942',
            ),
        )

    def _is_greeting_request(self, action: str) -> bool:
        return re.match(r'^(hi|hello|hey|namaste)\b', action) is not None or self._matches_command(
            action,
            exact=('\u0928\u092e\u0938\u094d\u0924\u0947',),
        )

    def _is_verification_menu_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_VERIFICATION, 'verify', 'verification', 'verification tools', 'वेरिफिकेशन', 'सत्यापन'),
            phrases=(
                'verify menu',
                'verification menu',
                'show verification',
                'open verification',
                'verify tools',
                'open verification tools',
                'show verification tools',
                'verification dikhao',
                'verification kholo',
                'verify dikhao',
                '\u0935\u0947\u0930\u093f\u092b\u093f\u0915\u0947\u0936\u0928',
                '\u0935\u0947\u0930\u093f\u092b\u093f\u0915\u0947\u0936\u0928 \u091f\u0942\u0932',
                'सत्यापन दिखाओ',
                'सत्यापन खोलो',
            ),
        )

    def _is_dashboard_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_DASHBOARD, 'dashboard', 'stats', 'overview', 'डैशबोर्ड'),
            phrases=(
                'show dashboard',
                'open dashboard',
                'my dashboard',
                'dashboard dikhao',
                'dashboard kholo',
                'sales dashboard',
                'sales stats',
                'show stats',
                'overview dikhao',
                'डैशबोर्ड दिखाओ',
                'डैशबोर्ड खोलो',
            ),
        )

    def _is_add_listing_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_ADD_LISTING, 'new', 'new listing', 'add listing', 'listing', 'लिस्टिंग'),
            phrases=(
                'create listing',
                'post listing',
                'add new listing',
                'new stock',
                'add stock',
                'listing add',
                'listing banao',
                'listing dalo',
                'nayi listing',
                'naya stock',
                '\u0928\u0908 \u0932\u093f\u0938\u094d\u091f\u093f\u0902\u0917',
                '\u0932\u093f\u0938\u094d\u091f\u093f\u0902\u0917 \u0921\u093e\u0932\u094b',
                'नई स्टॉक लिस्टिंग',
                'लिस्टिंग बनाओ',
            ),
        )

    def _is_listings_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_LISTINGS, 'listings', 'my listings', 'stock', 'लिस्टिंग्स', 'स्टॉक'),
            phrases=(
                'show listings',
                'open listings',
                'my stock',
                'live listings',
                'live stock',
                'stock dikhao',
                'listing dikhao',
                'meri listings',
                'mera stock',
                '\u0938\u094d\u091f\u0949\u0915 \u0926\u093f\u0916\u093e\u0913',
                '\u0932\u093f\u0938\u094d\u091f\u093f\u0902\u0917 \u0926\u093f\u0916\u093e\u0913',
                'लाइव लिस्टिंग',
                'लाइव स्टॉक',
            ),
        )

    def _is_orders_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_ORDERS, 'orders', 'my orders', 'ऑर्डर', 'ऑर्डर्स'),
            phrases=(
                'show orders',
                'open orders',
                'my order',
                'pending orders',
                'orders dikhao',
                'order dikhao',
                'mere orders',
                '\u0911\u0930\u094d\u0921\u0930 \u0926\u093f\u0916\u093e\u0913',
                'मेरे ऑर्डर',
                'ऑर्डर खोलो',
            ),
        )

    def _is_ledger_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_LEDGER, 'khata', 'ledger', 'bahi', 'baki', 'balance', 'dues', 'खाता', 'बाकी', 'उधार'),
            phrases=(
                'show khata',
                'open khata',
                'my khata',
                'khata dikhao',
                'khata kholo',
                'khata ledger',
                'show ledger',
                'ledger dikhao',
                'ledger kholo',
                'show balance',
                'balance dikhao',
                'show dues',
                'bahi dikhao',
                'mera khata',
                'udhar dikhao',
                '\u0916\u093e\u0924\u093e \u0926\u093f\u0916\u093e\u0913',
                '\u0916\u093e\u0924\u093e \u0916\u094b\u0932\u094b',
                '\u092c\u0939\u0940 \u0926\u093f\u0916\u093e\u0913',
                '\u0909\u0927\u093e\u0930 \u0926\u093f\u0916\u093e\u0913',
            ),
        )

    def _is_demand_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_DEMAND, 'demand', 'demands', 'demand pools', 'pool', 'pools', 'मांग', 'माँग'),
            phrases=(
                'show demand',
                'show demand pools',
                'buyer demand',
                'smart demand',
                'demand pool',
                'मांग दिखाओ',
                'माँग दिखाओ',
                'डिमांड दिखाओ',
                'डिमांड पूल',
            ),
        )

    def _is_customers_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_CUSTOMERS, 'customers', 'buyers', 'ग्राहक', 'खरीदार'),
            phrases=(
                'show customers',
                'open customers',
                'my customers',
                'show buyers',
                'buyers dikhao',
                'customer dikhao',
                'grahak dikhao',
                'mere customers',
                '\u0917\u094d\u0930\u093e\u0939\u0915 \u0926\u093f\u0916\u093e\u0913',
            ),
        )

    def _is_profile_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_PROFILE, 'profile', 'प्रोफाइल'),
            phrases=(
                'show profile',
                'open profile',
                'my profile',
                'seller profile',
                'profile dikhao',
                'mera profile',
                '\u092a\u094d\u0930\u094b\u092b\u093e\u0907\u0932 \u0926\u093f\u0916\u093e\u0913',
                'मेरी प्रोफाइल',
            ),
        )

    def _is_update_name_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_UPDATE_NAME, 'name', 'update name', 'change name'),
            phrases=(
                'seller name',
                'update my name',
                'change my name',
                'name badlo',
                'naam badlo',
                'mera naam badlo',
                '\u0928\u093e\u092e \u092c\u0926\u0932\u094b',
            ),
        )

    def _is_update_store_name_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_UPDATE_STORE_NAME, 'store', 'store name', 'farm name', 'update store', 'update store name'),
            phrases=(
                'change store name',
                'change farm name',
                'update farm name',
                'store badlo',
                'farm name badlo',
                'dukan name badlo',
                'dukkan name badlo',
                '\u0926\u0941\u0915\u093e\u0928 \u0928\u093e\u092e \u092c\u0926\u0932\u094b',
            ),
        )

    def _is_change_language_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(
                MENU_ACTION_CHANGE_LANGUAGE,
                'language',
                'change language',
                'update language',
                'bhasha',
                '\u092d\u093e\u0937\u093e',
                '\u092d\u093e\u0937\u093e \u092c\u0926\u0932\u0947\u0902',
            ),
            phrases=(
                'language change',
                'change my language',
                'language settings',
                'bhasha badlo',
                'apni bhasha badlo',
                'hindi karo',
                'english karo',
                '\u092d\u093e\u0937\u093e \u092c\u0926\u0932\u094b',
                '\u0939\u093f\u0902\u0926\u0940 \u0915\u0930\u094b',
                '\u0907\u0902\u0917\u094d\u0932\u093f\u0936 \u0915\u0930\u094b',
            ),
        )

    def _is_update_seller_type_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_UPDATE_SELLER_TYPE, 'type', 'seller type', 'update type', 'update seller type'),
            phrases=(
                'change seller type',
                'business type',
                'type badlo',
                'seller type badlo',
            ),
        )

    def _is_update_verification_method_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_UPDATE_VERIFICATION_METHOD, 'verify method', 'verification method', 'update verification method'),
            phrases=(
                'change verification method',
                'verify method badlo',
                'verification method badlo',
            ),
        )

    def _is_update_verification_number_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(
                MENU_ACTION_UPDATE_VERIFICATION_NUMBER,
                'verify id',
                'verification id',
                'verify number',
                'verification number',
                'update verification id',
            ),
            phrases=(
                'change verification id',
                'verify id badlo',
                'verification id badlo',
                'update verify id',
            ),
        )

    def _is_update_verification_proof_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(
                MENU_ACTION_UPDATE_VERIFICATION_PROOF,
                'verify proof',
                'verification proof',
                'update verification proof',
                'update proof',
            ),
            phrases=(
                'change verification proof',
                'verify proof badlo',
                'upload proof',
                'document proof',
            ),
        )

    def _is_update_location_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_UPDATE_LOCATION, 'location', 'update location'),
            phrases=(
                'change location',
                'pickup location',
                'update pickup location',
                'location badlo',
                'pickup badlo',
                '\u0932\u094b\u0915\u0947\u0936\u0928 \u092c\u0926\u0932\u094b',
            ),
        )

    def _is_help_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=(MENU_ACTION_HELP, 'help', 'मदद'),
            phrases=(
                'show help',
                'open help',
                'help dikhao',
                'madad',
                'madad chahiye',
                '\u092e\u0926\u0926',
            ),
        )

    def _is_deliveries_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=('deliveries', 'delivery'),
            phrases=(
                'show deliveries',
                'open deliveries',
                'my deliveries',
                'delivery status',
            ),
        )

    def _is_quality_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=('quality',),
            phrases=(
                'quality status',
                'show quality',
                'my quality',
            ),
        ) or action.startswith('quality ')

    def _is_status_request(self, action: str) -> bool:
        return self._matches_command(
            action,
            exact=('status',),
            phrases=(
                'show status',
                'my status',
                'seller status',
            ),
        )

    def _route_active_command(self, profile: SellerProfile, action: str) -> dict[str, Any] | None:
        if self._is_dashboard_request(action):
            return self._send_dashboard(profile)
        if self._is_add_listing_request(action):
            return self._prompt_for_listing(profile)
        if self._is_listings_request(action):
            return self._send_live_listings(profile)
        if self._is_orders_request(action):
            return self._send_orders(profile)
        if self._is_status_request(action):
            return self._send_status(profile)
        if self._is_deliveries_request(action):
            return self._send_deliveries(profile)
        if self._is_quality_request(action):
            return self._send_quality_status(profile, action=action)
        if self._is_ledger_request(action):
            return self._send_ledger(profile)
        if self._is_demand_request(action):
            return self._send_demand_pools(profile)
        if self._is_customers_request(action):
            return self._send_customers(profile)
        if self._is_profile_request(action):
            return self._send_profile(profile)
        if self._is_verification_menu_request(action):
            return self._send_verification_menu(profile)
        if self._is_update_name_request(action):
            return self._prompt_for_name_update(profile)
        if self._is_update_store_name_request(action):
            return self._prompt_for_store_name_update(profile)
        if self._is_change_language_request(action):
            return self._prompt_for_language_update(profile)
        if self._is_update_seller_type_request(action):
            return self._prompt_for_seller_type_update(profile)
        if self._is_update_verification_method_request(action):
            return self._prompt_for_verification_method_update(profile)
        if self._is_update_verification_number_request(action):
            return self._prompt_for_verification_number_update(profile)
        if self._is_update_verification_proof_request(action):
            return self._prompt_for_verification_proof_update(profile)
        if self._is_update_location_request(action):
            return self._prompt_for_location_update(profile)
        if self._is_help_request(action):
            return self._send_text(profile, self._copy(profile, 'help'), handled='seller_help')
        if self._is_greeting_request(action):
            return self._prompt_for_language_update(profile)
        if self._is_menu_request(action):
            return self._send_main_menu(profile)
        return None

    def _parse_order_decision(self, action: str) -> tuple[str, int | None, str | None] | None:
        accept_words = {'yes', 'y', 'accept', 'accepted', 'haan', 'ha', 'हाँ', 'हा'}
        reject_words = {'no', 'n', 'reject', 'rejected', 'nahi', 'nahin', 'नहीं', 'नही'}

        explicit_match = re.match(r'^(accept|reject)\s+order\s+([a-z0-9_:-]+)$', action)
        if explicit_match is not None:
            return (explicit_match.group(1), None, explicit_match.group(2))

        if action.startswith('order_accept:'):
            order_id = action.split(':', 1)[1].strip()
            if order_id:
                return ('accept', None, order_id)
        if action.startswith('order_reject:'):
            order_id = action.split(':', 1)[1].strip()
            if order_id:
                return ('reject', None, order_id)

        def parse_number(value: str) -> int | None:
            cleaned = value.strip().strip('.,:;()[]{}').lstrip('#').strip().strip('.,:;()[]{}')
            return int(cleaned) if cleaned.isdigit() else None

        for word in accept_words:
            if action == word:
                return ('accept', None, None)
            if action.startswith(f'{word} '):
                order_number = parse_number(action[len(word):])
                if order_number is not None:
                    return ('accept', order_number, None)
            if action.endswith(f' {word}'):
                order_number = parse_number(action[:-len(word)])
                if order_number is not None:
                    return ('accept', order_number, None)

        for word in reject_words:
            if action == word:
                return ('reject', None, None)
            if action.startswith(f'{word} '):
                order_number = parse_number(action[len(word):])
                if order_number is not None:
                    return ('reject', order_number, None)
            if action.endswith(f' {word}'):
                order_number = parse_number(action[:-len(word)])
                if order_number is not None:
                    return ('reject', order_number, None)

        return None

    def _seller_orders(self, seller_id: str) -> list[Any]:
        list_orders = getattr(self.store, 'list_orders', None)
        if list_orders is None:
            return []
        return [
            order
            for order in list_orders()
            if order.seller_id == seller_id
        ]

    def _recent_orders(self, seller_id: str) -> list[Any]:
        return sorted(self._seller_orders(seller_id), key=lambda order: order.created_at, reverse=True)[:5]

    def _seller_deliveries(self, seller_id: str) -> list[Any]:
        list_deliveries = getattr(self.marketplace, 'list_deliveries', None)
        if not callable(list_deliveries):
            return []
        return list_deliveries(seller_id=seller_id)

    def _active_seller_deliveries(self, seller_id: str) -> list[Any]:
        closed_statuses = {'delivered', 'buyer_confirmed', 'settled', 'cancelled'}
        return [
            delivery
            for delivery in self._seller_deliveries(seller_id)
            if getattr(delivery, 'status', '') not in closed_statuses
        ]

    def _find_seller_delivery(self, seller_id: str, delivery_id: str) -> Any | None:
        for delivery in self._seller_deliveries(seller_id):
            if delivery.id == delivery_id:
                return delivery
        return None

    def _delivery_next_seller_action(self, status: str) -> tuple[str, str] | None:
        canonical = getattr(self.marketplace, '_canonical_delivery_status', lambda value: value)(status)
        next_actions = {
            'order_accepted': ('packed', 'Pack'),
            'quality_approved': ('packed', 'Pack'),
            'packed': ('handover_pending', 'Handover'),
        }
        return next_actions.get(canonical)

    def _parse_delivery_command(self, action: str) -> tuple[str, str] | None:
        if action.startswith('delivery_advance:'):
            parts = action.split(':', 2)
            if len(parts) == 3 and parts[1] and parts[2]:
                command = 'handover' if parts[2] == 'handover' else parts[2]
                return parts[1], command
        if action.startswith('delivery_cancel:'):
            delivery_id = action.split(':', 1)[1].strip()
            if delivery_id:
                return delivery_id, 'cancel'

        match = re.match(r'^delivery\s+([a-z0-9_:-]+)\s+(packed|handover|cancel)$', action)
        if match is not None:
            return match.group(1), match.group(2)
        return None

    def _send_deliveries(self, profile: SellerProfile) -> dict[str, Any]:
        deliveries = self._active_seller_deliveries(profile.seller_id)
        if not deliveries:
            return self._send_text(profile, self._copy(profile, 'deliveries_empty'), handled='seller_deliveries')

        body_lines = [self._copy(profile, 'delivery_status_title')]
        rows: list[dict[str, str]] = []
        for delivery in deliveries[:5]:
            quantity = f'{delivery.quantity_kg:g}'
            current_status = str(getattr(delivery, 'status', '')).replace('_', ' ')
            body_lines.append(
                f'- {delivery.id}: {delivery.product_name}, {delivery.buyer_name}, {quantity} kg, {current_status}'
            )
            next_action = self._delivery_next_seller_action(getattr(delivery, 'status', ''))
            if next_action is not None:
                action_status, action_label = next_action
                action_id = 'handover' if action_status == 'handover_pending' else action_status
                body_lines.append(f'  Next action: {action_label}')
                rows.append({
                    'id': f'delivery_advance:{delivery.id}:{action_id}',
                    'title': f'{action_label} {quantity}kg',
                    'description': f'{delivery.product_name} for {delivery.buyer_name}',
                })
            rows.append({
                'id': f'delivery_cancel:{delivery.id}',
                'title': f'Cancel {quantity}kg',
                'description': f'{delivery.product_name} for {delivery.buyer_name}',
            })

        body_lines.append('Reply: delivery <id> packed | handover | cancel')
        result = self.whatsapp.send_list_message(
            to=profile.seller_id,
            body='\n'.join(body_lines[:12]),
            button_text='Deliveries',
            sections=[{'title': 'Delivery actions', 'rows': rows[:10]}],
        )
        if not result.get('sent'):
            self.whatsapp.send_text_message(to=profile.seller_id, body='\n'.join(body_lines))
        return {'ok': True, 'handled': 'seller_deliveries'}

    def _send_quality_status(self, profile: SellerProfile, *, action: str) -> dict[str, Any]:
        listings = [
            listing
            for listing in self.store.list_listings()
            if listing.seller_id == profile.seller_id
        ]
        if not listings:
            return self._send_text(profile, self._copy(profile, 'quality_empty'), handled='seller_quality_status')

        target_listing = None
        parts = action.split()
        if len(parts) >= 2:
            listing_id = parts[1]
            target_listing = next((listing for listing in listings if listing.id == listing_id), None)
            listings = [target_listing] if target_listing is not None else []

        if not listings:
            return self._send_text(profile, self._copy(profile, 'quality_empty'), handled='seller_quality_status')

        lines = ['Your quality checks:']
        for index, listing in enumerate(sorted(listings, key=lambda item: item.created_at, reverse=True)[:5], start=1):
            quality_label = listing.quality_status.title()
            grade = f' Grade {listing.quality_grade}' if listing.quality_status == 'approved' and listing.quality_grade in {'A', 'B', 'C'} else ''
            note = f' - {listing.quality_notes}' if listing.quality_notes else ''
            lines.append(f'{index}. {listing.product_name} {listing.available_kg:g} kg - {quality_label}{grade}{note}')
        return self._send_text(profile, '\n'.join(lines), handled='seller_quality_status')

    def _send_status(self, profile: SellerProfile) -> dict[str, Any]:
        listings = [listing for listing in self.store.list_listings() if listing.seller_id == profile.seller_id and listing.status == 'live']
        pending_quality = [listing for listing in listings if listing.quality_status == 'pending']
        pending_orders = [order for order in self._seller_orders(profile.seller_id) if order.status == 'pending']
        deliveries = self._active_seller_deliveries(profile.seller_id)
        ledger = self.marketplace.build_seller_ledger(profile.seller_id)
        outstanding = ledger.summary.total_outstanding_amount if ledger is not None else 0

        body = (
            f"{self._copy(profile, 'status_title')}\n"
            f"- Active listings: {len(listings)}\n"
            f"- Pending quality checks: {len(pending_quality)}\n"
            f"- Pending orders: {len(pending_orders)}\n"
            f"- Active deliveries: {len(deliveries)}\n"
            f"- Outstanding khata: Rs {outstanding:g}"
        )
        return self._send_text(profile, body, handled='seller_status')

    def _handle_delivery_command(self, *, profile: SellerProfile, delivery_id: str, command: str) -> dict[str, Any] | None:
        delivery = self._find_seller_delivery(profile.seller_id, delivery_id)
        if delivery is None:
            return self._send_text(profile, self._copy(profile, 'delivery_not_found'), handled='seller_delivery_not_found')

        status_map = {
            'packed': 'packed',
            'handover': 'handover_pending',
            'cancel': 'cancelled',
        }
        next_status = status_map.get(command)
        if next_status is None:
            return None

        try:
            updated = self.marketplace.advance_delivery_for_actor(
                delivery.id,
                DeliveryAdvanceRequestIn(
                    next_status=next_status,
                    actor_role='seller',
                    actor_id=profile.seller_id,
                ),
            )
        except ValueError:
            return self._send_text(profile, self._copy(profile, 'delivery_invalid_transition'), handled='seller_delivery_invalid_transition')

        body = (
            f'Delivery updated: {updated.product_name} for {updated.buyer_name} is now {updated.status.replace("_", " ")}.'
            if not self._is_hindi(profile)
            else f'Delivery update ho gayi: {updated.product_name} for {updated.buyer_name} ab {updated.status.replace("_", " ")} hai.'
        )
        self.whatsapp.send_text_message(to=profile.seller_id, body=body)
        return {'ok': True, 'handled': 'seller_delivery_updated'}

    def _find_seller_order(self, seller_id: str, order_id: str) -> Any | None:
        for order in self._seller_orders(seller_id):
            if order.id == order_id:
                return order
        return None

    def _order_product_name(self, order: Any) -> str:
        product_name = str(getattr(order, 'product_name', '') or '').strip()
        if product_name and product_name != 'items':
            return product_name

        get_listing = getattr(self.store, 'get_listing', None)
        if get_listing is not None:
            listing = get_listing(order.listing_id)
            if listing is not None:
                listing_product = str(getattr(listing, 'product_name', '') or '').strip()
                if listing_product:
                    return listing_product

        return 'items'

    def _latest_pending_order_id(self, seller_id: str) -> str | None:
        pending_orders = [
            order
            for order in self._seller_orders(seller_id)
            if order.status == 'pending'
        ]
        if not pending_orders:
            return None
        latest_order = max(pending_orders, key=lambda order: order.created_at)
        return latest_order.id

    def _handle_order_decision(
        self,
        *,
        profile: SellerProfile,
        decision: str,
        order_number: int | None,
        order_id: str | None,
    ) -> dict[str, Any] | None:
        if order_id is not None:
            selected_order = self._find_seller_order(profile.seller_id, order_id)
            if selected_order is None:
                body = (
                    'à¤‘à¤°à¥à¤¡à¤° à¤¨à¤¹à¥€à¤‚ à¤®à¤¿à¤²à¤¾à¥¤ ORDERS à¤²à¤¿à¤–à¤•à¤° à¤¹à¤¾à¤² à¤•à¥‡ à¤‘à¤°à¥à¤¡à¤° à¤¦à¥‡à¤–à¥‡à¤‚à¥¤'
                    if self._is_hindi(profile)
                    else 'Order was not found. Reply ORDERS to see recent orders.'
                )
                return self._send_text(profile, body, handled='seller_order_not_found')
            if selected_order.status != 'pending':
                body = (
                    f'à¤‘à¤°à¥à¤¡à¤° à¤ªà¤¹à¤²à¥‡ à¤¸à¥‡ {selected_order.status.upper()} à¤¹à¥ˆà¥¤'
                    if self._is_hindi(profile)
                    else f'Order is already {selected_order.status.upper()}.'
                )
                return self._send_text(profile, body, handled='seller_order_already_decided')
        elif order_number is not None:
            recent_orders = self._recent_orders(profile.seller_id)
            if order_number < 1 or order_number > len(recent_orders):
                body = (
                    f'ऑर्डर #{order_number} नहीं मिला। ORDERS लिखकर हाल के ऑर्डर देखें।'
                    if self._is_hindi(profile)
                    else f'Order #{order_number} was not found. Reply ORDERS to see recent orders.'
                )
                return self._send_text(profile, body, handled='seller_order_not_found')
            selected_order = recent_orders[order_number - 1]
            order_id = selected_order.id
            if selected_order.status != 'pending':
                body = (
                    f'ऑर्डर #{order_number} पहले से {selected_order.status.upper()} है।'
                    if self._is_hindi(profile)
                    else f'Order #{order_number} is already {selected_order.status.upper()}.'
                )
                return self._send_text(profile, body, handled='seller_order_already_decided')
        else:
            order_id = self._latest_pending_order_id(profile.seller_id)

        if order_id is None:
            body = (
                'अभी कोई लंबित ऑर्डर नहीं है। ORDERS लिखकर हाल के ऑर्डर देखें।'
                if self._is_hindi(profile)
                else 'No pending orders right now. Reply ORDERS to see recent orders.'
            )
            return self._send_text(profile, body, handled='seller_order_not_found')

        order = self.marketplace.respond_to_order(order_id=order_id, decision=decision)
        order_label = f' #{order_number}' if order_number is not None else ''
        quantity = f'{order.quantity_kg:g}'
        product_name = self._order_product_name(order)
        if decision == 'accept':
            body = (
                f'ऑर्डर स्वीकार हो गया। {quantity} किलो, पिकअप {order.pickup_time}।'
                if self._is_hindi(profile)
                else f'Order{order_label} accepted. {quantity} kg {product_name}, pickup {order.pickup_time}.'
            )
            handled = 'seller_order_accepted'
        else:
            body = (
                f'ऑर्डर अस्वीकार हो गया। {quantity} किलो, पिकअप {order.pickup_time}।'
                if self._is_hindi(profile)
                else f'Order{order_label} rejected. {quantity} kg {product_name}, pickup {order.pickup_time}.'
            )
            handled = 'seller_order_rejected'
        return self._send_text(profile, body, handled=handled)

    def _prompt_for_listing(self, profile: SellerProfile) -> dict[str, Any]:
        self._save_session(profile.seller_id, 'awaiting_listing_message')
        return self._send_text(
            profile,
            f"{self._copy(profile, 'listing_prompt')}\n{self._copy(profile, 'listing_prompt_short')}",
            handled='seller_listing_prompt',
        )

    def _prompt_for_location_update(self, profile: SellerProfile) -> dict[str, Any]:
        self._save_session(profile.seller_id, 'awaiting_store_location')
        return self._send_text(profile, self._copy(profile, 'location_prompt'), handled='seller_location_prompt')

    def _prompt_for_name_update(self, profile: SellerProfile) -> dict[str, Any]:
        self._save_session(profile.seller_id, 'awaiting_profile_name_update')
        return self._send_text(profile, self._copy(profile, 'name_prompt'), handled='seller_name_prompt')

    def _prompt_for_store_name_update(self, profile: SellerProfile) -> dict[str, Any]:
        self._save_session(profile.seller_id, 'awaiting_store_name_update')
        return self._send_text(profile, self._copy(profile, 'store_name_prompt'), handled='seller_store_name_prompt')

    def _prompt_for_language_update(self, profile: SellerProfile) -> dict[str, Any]:
        self._save_session(profile.seller_id, 'awaiting_language_update')
        if not self._claim_response_fingerprint(
            profile.seller_id,
            'language_prompt',
            window_seconds=LANGUAGE_PROMPT_DEDUP_WINDOW_SECONDS,
        ):
            return {'ok': True, 'ignored': True, 'reason': 'duplicate_language_prompt'}
        result = self.whatsapp.send_reply_buttons(
            to=profile.seller_id,
            body=self._copy(profile, 'language_prompt'),
            buttons=[
                {'id': 'lang_hi', 'title': 'हिंदी'},
                {'id': 'lang_en', 'title': 'English'},
            ],
        )
        if not result.get('sent'):
            fallback = (
                'à¤­à¤¾à¤·à¤¾ à¤šà¥à¤¨à¥‡à¤‚: HINDI à¤¯à¤¾ ENGLISH'
                if profile.preferred_language == 'hi'
                else 'Choose your language: HINDI or ENGLISH'
            )
            self.whatsapp.send_text_message(to=profile.seller_id, body=fallback)
        return {'ok': True, 'handled': 'seller_language_prompt'}

    def _prompt_for_seller_type_update(self, profile: SellerProfile) -> dict[str, Any]:
        return self._send_seller_type_prompt(
            profile,
            state='awaiting_seller_type_update',
            handled='seller_type_update_prompt',
        )

    def _send_seller_type_prompt(self, profile: SellerProfile, *, state: str, handled: str) -> dict[str, Any]:
        self._save_session(profile.seller_id, state)
        if self._is_hindi(profile):
            sections = [
                {
                    'title': 'विक्रेता प्रकार',
                    'rows': [
                        {'id': 'seller_farmer', 'title': 'किसान', 'description': 'व्यक्तिगत किसान या फार्म मालिक'},
                        {'id': 'seller_aggregator', 'title': 'एग्रीगेटर', 'description': 'कई विक्रेताओं से उपज इकट्ठा करता है'},
                        {'id': 'seller_fpo', 'title': 'FPO', 'description': 'किसान उत्पादक संगठन'},
                        {'id': 'seller_trader', 'title': 'ट्रेडर', 'description': 'थोक व्यापारी या मंडी ऑपरेटर'},
                    ],
                },
            ]
        else:
            sections = [
                {
                    'title': 'Seller types',
                    'rows': [
                        {'id': 'seller_farmer', 'title': 'Farmer', 'description': 'Individual grower or farm owner'},
                        {'id': 'seller_aggregator', 'title': 'Aggregator', 'description': 'Collects produce from many sellers'},
                        {'id': 'seller_fpo', 'title': 'FPO', 'description': 'Farmer producer organization'},
                        {'id': 'seller_trader', 'title': 'Trader', 'description': 'Wholesale trader or mandi operator'},
                    ],
                },
            ]
        result = self.whatsapp.send_list_message(
            to=profile.seller_id,
            body=self._copy(profile, 'ask_seller_type'),
            button_text=self._copy(profile, 'seller_type_button'),
            sections=sections,
        )
        if not result.get('sent'):
            fallback_commands = (
                'जवाब दें: FARMER, AGGREGATOR, FPO, TRADER'
                if self._is_hindi(profile)
                else 'Reply with: FARMER, AGGREGATOR, FPO, TRADER'
            )
            fallback = (
                f"{self._copy(profile, 'ask_seller_type')}\n\n"
                f'{fallback_commands}'
            )
            self.whatsapp.send_text_message(to=profile.seller_id, body=fallback)
        return {'ok': True, 'handled': handled}

    def _prompt_for_verification_method_update(self, profile: SellerProfile) -> dict[str, Any]:
        return self._send_verification_method_prompt(
            profile,
            state='awaiting_verification_method_update',
            handled='seller_verification_method_update_prompt',
        )

    def _prompt_for_verification_number_update(self, profile: SellerProfile) -> dict[str, Any]:
        self._save_session(profile.seller_id, 'awaiting_verification_number_update')
        return self._send_text(profile, self._copy(profile, 'verification_number_prompt'), handled='seller_verification_number_prompt')

    def _prompt_for_verification_proof_update(self, profile: SellerProfile) -> dict[str, Any]:
        self._save_session(profile.seller_id, 'awaiting_verification_proof_update')
        return self._send_text(profile, self._copy(profile, 'verification_proof_prompt'), handled='seller_verification_proof_prompt')

    def _handle_listing_session_interrupt(
        self,
        *,
        profile: SellerProfile,
        session: SellerSession | None,
        action: str,
    ) -> dict[str, Any] | None:
        if session is None or session.state not in LISTING_SESSION_STATES:
            return None

        self._clear_session(profile.seller_id)
        routed_command = self._route_active_command(profile, action)
        if routed_command is not None:
            return routed_command
        return None

    def _handle_profile_name_update(self, *, profile: SellerProfile, raw_text: str) -> dict[str, Any]:
        cleaned = raw_text.strip()
        if self._normalize_text(cleaned) == 'cancel':
            self._clear_session(profile.seller_id)
            return self._send_main_menu(profile)
        if not cleaned:
            return self._send_text(profile, self._copy(profile, 'name_prompt'), handled='seller_name_prompt')

        profile.seller_name = cleaned
        profile.updated_at = datetime.utcnow()
        self.store.save_seller_profile(profile)
        self._clear_session(profile.seller_id)
        self.whatsapp.send_text_message(to=profile.seller_id, body=self._copy(profile, 'name_updated'))
        self._send_main_menu(profile)
        return {'ok': True, 'handled': 'seller_name_updated'}

    def _handle_store_name_update(self, *, profile: SellerProfile, raw_text: str) -> dict[str, Any]:
        cleaned = raw_text.strip()
        if self._normalize_text(cleaned) == 'cancel':
            self._clear_session(profile.seller_id)
            return self._send_main_menu(profile)
        if not cleaned:
            return self._send_text(profile, self._copy(profile, 'store_name_prompt'), handled='seller_store_name_prompt')

        profile.store_name = cleaned
        profile.updated_at = datetime.utcnow()
        self.store.save_seller_profile(profile)
        self._clear_session(profile.seller_id)
        self.whatsapp.send_text_message(to=profile.seller_id, body=self._copy(profile, 'store_name_updated'))
        self._send_main_menu(profile)
        return {'ok': True, 'handled': 'seller_store_name_updated'}

    def _handle_language_update(self, *, profile: SellerProfile, action: str) -> dict[str, Any]:
        if action == 'cancel':
            self._clear_session(profile.seller_id)
            return self._send_main_menu(profile)

        language = self._parse_language(action)
        if language is None:
            self._clear_session(profile.seller_id)
            routed_command = self._route_active_command(profile, action)
            if routed_command is not None:
                return routed_command
            return self._send_main_menu(profile)

        profile.preferred_language = language  # type: ignore[assignment]
        profile.updated_at = datetime.utcnow()
        self.store.save_seller_profile(profile)
        self._clear_session(profile.seller_id)
        return self._send_main_menu(profile)

    def _handle_seller_type_update(self, *, profile: SellerProfile, action: str) -> dict[str, Any]:
        if action == 'cancel':
            self._clear_session(profile.seller_id)
            return self._send_main_menu(profile)

        seller_type = self._parse_seller_type(action)
        if seller_type is None:
            return self._prompt_for_seller_type_update(profile)

        profile.seller_type = seller_type
        profile.updated_at = datetime.utcnow()
        self.store.save_seller_profile(profile)
        self._clear_session(profile.seller_id)
        self.whatsapp.send_text_message(to=profile.seller_id, body=self._copy(profile, 'seller_type_updated'))
        self._send_main_menu(profile)
        return {'ok': True, 'handled': 'seller_type_updated'}

    def _handle_verification_method_update(self, *, profile: SellerProfile, action: str) -> dict[str, Any]:
        if action == 'cancel':
            self._clear_session(profile.seller_id)
            return self._send_main_menu(profile)

        verification_method = self._parse_verification_method(action)
        if verification_method is None:
            return self._prompt_for_verification_method_update(profile)

        profile.verification_method = verification_method
        profile.updated_at = datetime.utcnow()
        self.store.save_seller_profile(profile)
        self._clear_session(profile.seller_id)
        self.whatsapp.send_text_message(to=profile.seller_id, body=self._copy(profile, 'verification_method_updated'))
        self._send_main_menu(profile)
        return {'ok': True, 'handled': 'seller_verification_method_updated'}

    def _handle_verification_number_update(self, *, profile: SellerProfile, action: str, raw_text: str) -> dict[str, Any]:
        if action == 'cancel':
            self._clear_session(profile.seller_id)
            return self._send_main_menu(profile)

        cleaned = raw_text.strip()
        if action == 'skip':
            profile.verification_number = None
        elif not cleaned:
            return self._send_text(profile, self._copy(profile, 'verification_number_prompt'), handled='seller_verification_number_prompt')
        else:
            profile.verification_number = cleaned

        profile.updated_at = datetime.utcnow()
        self.store.save_seller_profile(profile)
        self._clear_session(profile.seller_id)
        self.whatsapp.send_text_message(to=profile.seller_id, body=self._copy(profile, 'verification_number_updated'))
        self._send_main_menu(profile)
        return {'ok': True, 'handled': 'seller_verification_number_updated'}

    def _handle_verification_proof_update(
        self,
        *,
        profile: SellerProfile,
        action: str,
        raw_text: str,
        image_url: str | None,
    ) -> dict[str, Any]:
        if action == 'cancel' and not image_url:
            self._clear_session(profile.seller_id)
            return self._send_main_menu(profile)
        if action == 'skip' and not image_url:
            profile.verification_proof_url = None
            profile.verification_status = 'manual_review'
            profile.verification_notes = 'Verification proof cleared through WhatsApp profile management'
        else:
            proof_value = (image_url or raw_text or '').strip()
            if not proof_value:
                return self._send_text(profile, self._copy(profile, 'verification_proof_prompt'), handled='seller_verification_proof_prompt')
            profile.verification_proof_url = proof_value
            profile.verification_status = 'verified' if image_url else 'manual_review'
            profile.verification_notes = 'Verification proof updated through WhatsApp profile management'

        profile.updated_at = datetime.utcnow()
        self.store.save_seller_profile(profile)
        self._clear_session(profile.seller_id)
        self.whatsapp.send_text_message(to=profile.seller_id, body=self._copy(profile, 'verification_proof_updated'))
        self._send_main_menu(profile)
        return {'ok': True, 'handled': 'seller_verification_proof_updated'}

    def _handle_location_update(self, *, profile: SellerProfile, raw_text: str) -> dict[str, Any]:
        location = raw_text.strip()
        if self._normalize_text(location) == 'cancel':
            self._clear_session(profile.seller_id)
            return self._send_main_menu(profile)
        if not location:
            return self._send_text(profile, self._copy(profile, 'location_prompt'), handled='seller_location_prompt')
        geocoded = self.geo.geocode(location)
        profile.default_pickup_location = geocoded['pickup_location'] if geocoded else location
        profile.latitude = geocoded.get('latitude') if geocoded else None
        profile.longitude = geocoded.get('longitude') if geocoded else None
        profile.place_id = geocoded.get('place_id') if geocoded else None
        profile.updated_at = datetime.utcnow()
        self.store.save_seller_profile(profile)
        self._clear_session(profile.seller_id)
        self.whatsapp.send_text_message(to=profile.seller_id, body=self._copy(profile, 'location_updated'))
        self._send_main_menu(profile)
        return {'ok': True, 'handled': 'seller_location_updated'}

    def _handle_listing_capture(
        self,
        *,
        profile: SellerProfile,
        session: SellerSession,
        raw_text: str,
        image_url: str | None,
        quality_assessment: ProduceQualityAssessment | None,
        image_bytes: bytes | None,
        image_mime_type: str | None,
        capture_mode: LedgerCaptureMode,
    ) -> dict[str, Any]:
        cleaned = raw_text.strip()
        effective_capture_mode = self._effective_listing_capture_mode(session, capture_mode)
        if self._normalize_text(cleaned) == 'cancel':
            self._clear_session(profile.seller_id)
            return self._send_main_menu(profile)
        if session.draft_message and effective_capture_mode == 'voice_note':
            merged_draft = self._merge_listing_correction(session.draft_message, cleaned)
            return self._prompt_for_listing_confirmation(
                profile=profile,
                draft_message=merged_draft,
                quality_assessment=quality_assessment,
                capture_mode=effective_capture_mode,
                draft_image_url=self._listing_image_url(
                    session=session,
                    image_url=image_url,
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                ),
            )
        if not cleaned and image_url:
            return self._prompt_for_photo_listing(
                profile=profile,
                quality_assessment=quality_assessment,
                image_url=image_url,
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
            )
        if not self._has_listing_signal(cleaned):
            return self._continue_listing_draft(
                profile=profile,
                draft_message=cleaned,
                image_url=self._listing_image_url(
                    session=session,
                    image_url=image_url,
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                ),
                quality_assessment=quality_assessment,
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                capture_mode=effective_capture_mode,
            )
        return self._prompt_for_listing_confirmation(
            profile=profile,
            draft_message=cleaned,
            quality_assessment=quality_assessment,
            capture_mode=effective_capture_mode,
            draft_image_url=self._listing_image_url(
                session=session,
                image_url=image_url,
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
            ),
        )

    def _handle_listing_slot_capture(
        self,
        *,
        profile: SellerProfile,
        session: SellerSession,
        raw_text: str,
        image_url: str | None,
        quality_assessment: ProduceQualityAssessment | None,
        image_bytes: bytes | None,
        image_mime_type: str | None,
        capture_mode: LedgerCaptureMode,
    ) -> dict[str, Any]:
        cleaned = raw_text.strip()
        effective_capture_mode = self._effective_listing_capture_mode(session, capture_mode)
        if self._normalize_text(cleaned) == 'cancel':
            self._clear_session(profile.seller_id)
            return self._send_main_menu(profile)

        reply = self._format_listing_slot_reply(session.state, cleaned)
        draft_message = ' '.join(part for part in [session.draft_message, reply] if part).strip()
        return self._continue_listing_draft(
            profile=profile,
            draft_message=draft_message,
            image_url=self._listing_image_url(
                session=session,
                image_url=image_url,
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
            ),
            quality_assessment=quality_assessment,
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            capture_mode=effective_capture_mode,
        )

    def _format_listing_slot_reply(self, state: str, raw_text: str) -> str:
        normalized = self._normalize_text(raw_text)
        if re.fullmatch(r'\d+(?:\.\d+)?', normalized):
            if state == 'awaiting_listing_price':
                return f'{normalized} rupees kilo'
            if state == 'awaiting_listing_quantity':
                return f'{normalized} kilo'
        return raw_text

    def _listing_signals(self, message_text: str) -> dict[str, Any]:
        extractor = getattr(self.marketplace, 'extractor', None)
        if extractor is not None and hasattr(extractor, 'parse_listing_signals'):
            return extractor.parse_listing_signals(message_text)

        normalized = self._normalize_text(message_text)
        quantity_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilo|kilogram)', normalized)
        price_match = re.search(r'(?:rs|rupees|rupay|rupaye)\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:rs|rupees|rupay|rupaye|per)', normalized)
        return {
            'product_name': None,
            'category': None,
            'quantity_kg': float(quantity_match.group(1)) if quantity_match else None,
            'price_per_kg': float(next(group for group in price_match.groups() if group)) if price_match else None,
            'pickup_location': None,
        }

    def _apply_visual_product_hint(
        self,
        draft_message: str,
        quality_assessment: ProduceQualityAssessment | None,
    ) -> str:
        cleaned = draft_message.strip()
        detected_product = (quality_assessment.detected_product_name or '').strip() if quality_assessment else ''
        if not cleaned or not detected_product:
            return cleaned

        signals = self._listing_signals(cleaned)
        if signals.get('product_name'):
            return cleaned
        return f'{detected_product} {cleaned}'.strip()

    def _continue_listing_draft(
        self,
        *,
        profile: SellerProfile,
        draft_message: str,
        image_url: str | None,
        quality_assessment: ProduceQualityAssessment | None,
        image_bytes: bytes | None,
        image_mime_type: str | None,
        capture_mode: LedgerCaptureMode,
    ) -> dict[str, Any]:
        cleaned = draft_message.strip()
        if not cleaned:
            if image_url:
                return self._prompt_for_photo_listing(
                    profile=profile,
                    quality_assessment=quality_assessment,
                    image_url=image_url,
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                )
            return self._send_text(profile, self._copy(profile, 'listing_prompt_short'), handled='seller_listing_retry')

        cleaned = self._apply_visual_product_hint(cleaned, quality_assessment)

        if self._has_listing_signal(cleaned):
            return self._prompt_for_listing_confirmation(
                profile=profile,
                draft_message=cleaned,
                quality_assessment=quality_assessment,
                capture_mode=capture_mode,
                draft_image_url=self._listing_image_url(
                    session=None,
                    image_url=image_url,
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                ),
            )

        signals = self._listing_signals(cleaned)
        has_any_listing_detail = bool(signals.get('product_name') or signals.get('quantity_kg') or signals.get('price_per_kg'))
        if not has_any_listing_detail:
            return self._send_text(profile, self._copy(profile, 'listing_prompt_short'), handled='seller_listing_retry')

        if not signals.get('product_name'):
            return self._prompt_for_listing_slot(
                profile=profile,
                state='awaiting_listing_product',
                draft_message=cleaned,
                quality_assessment=quality_assessment,
                capture_mode=capture_mode,
                draft_image_url=image_url,
            )
        if not signals.get('quantity_kg'):
            return self._prompt_for_listing_slot(
                profile=profile,
                state='awaiting_listing_quantity',
                draft_message=cleaned,
                quality_assessment=quality_assessment,
                capture_mode=capture_mode,
                draft_image_url=image_url,
            )
        return self._prompt_for_listing_slot(
            profile=profile,
            state='awaiting_listing_price',
            draft_message=cleaned,
            quality_assessment=quality_assessment,
            capture_mode=capture_mode,
            draft_image_url=image_url,
        )

    def _prompt_for_listing_slot(
        self,
        *,
        profile: SellerProfile,
        state: str,
        draft_message: str,
        quality_assessment: ProduceQualityAssessment | None,
        capture_mode: LedgerCaptureMode,
        draft_image_url: str | None = None,
    ) -> dict[str, Any]:
        self._save_session(
            profile.seller_id,
            state,
            draft_message=draft_message,
            quality_assessment=quality_assessment,
            draft_capture_mode=capture_mode,
            draft_image_url=draft_image_url,
        )
        signals = self._listing_signals(draft_message)
        product_name = signals.get('product_name') or 'this product'
        quantity_kg = signals.get('quantity_kg')

        if state == 'awaiting_listing_product':
            body = (
                'यह लिस्टिंग किस प्रोडक्ट के लिए है? उदाहरण: बैंगन, आलू, टमाटर।'
                if self._is_hindi(profile)
                else 'Which product is this listing for? Example: baingan, potato, tomato.'
            )
        elif state == 'awaiting_listing_quantity':
            body = (
                f'{product_name} कितना किलो है? उदाहरण: 40 किलो।'
                if self._is_hindi(profile)
                else f'How many kg of {product_name} do you have? Example: 40 kilo.'
            )
        else:
            quantity_text = f'{quantity_kg:g} kg ' if isinstance(quantity_kg, float) else ''
            body = (
                f'{quantity_text}{product_name} का प्रति किलो क्या भाव है? उदाहरण: 30 रुपये किलो।'
                if self._is_hindi(profile)
                else f'What price per kg for {quantity_text}{product_name}? Example: 30 rupees kilo.'
            )
        return self._send_text(profile, body, handled='seller_listing_slot_prompt')

    def _prompt_for_listing_confirmation(
        self,
        *,
        profile: SellerProfile,
        draft_message: str,
        quality_assessment: ProduceQualityAssessment | None,
        capture_mode: LedgerCaptureMode,
        draft_image_url: str | None = None,
    ) -> dict[str, Any]:
        cleaned = draft_message.strip()
        self._save_session(
            profile.seller_id,
            'awaiting_listing_confirmation',
            draft_message=cleaned,
            quality_assessment=quality_assessment,
            draft_capture_mode=capture_mode,
            draft_image_url=draft_image_url,
        )
        body = self._format_listing_confirmation_body(profile, cleaned)
        result = self.whatsapp.send_reply_buttons(
            to=profile.seller_id,
            body=body,
            buttons=[
                {'id': LISTING_ACTION_CONFIRM_LIVE, 'title': 'लाइव करें' if self._is_hindi(profile) else 'Make live'},
                {'id': LISTING_ACTION_EDIT, 'title': 'बदलें' if self._is_hindi(profile) else 'Edit'},
            ],
        )
        if not result.get('sent'):
            fallback = (
                f'{body}\n\nलाइव करने के लिए LIVE लिखें, या सुधारने के लिए EDIT लिखें।'
                if self._is_hindi(profile)
                else f'{body}\n\nReply LIVE to make it live, or EDIT to correct it.'
            )
            self.whatsapp.send_text_message(to=profile.seller_id, body=fallback)
        return {'ok': True, 'handled': 'seller_listing_review'}

    def _format_listing_confirmation_body(self, profile: SellerProfile, draft_message: str) -> str:
        signals = self._listing_signals(draft_message)
        product_name = signals.get('product_name') or 'Unknown product'
        quantity_kg = signals.get('quantity_kg')
        price_per_kg = signals.get('price_per_kg')
        quantity_text = f'{quantity_kg:g} kg' if isinstance(quantity_kg, float) else '-'
        price_text = f'Rs {price_per_kg:g}/kg' if isinstance(price_per_kg, float) else '-'
        pickup_text = signals.get('pickup_location')
        if not pickup_text or pickup_text == DEFAULT_PICKUP_LOCATION:
            pickup_text = profile.default_pickup_location or DEFAULT_PICKUP_LOCATION
        price_reference = self._listing_price_reference(
            product_name=product_name,
            quality_grade=None,
            seller_price_per_kg=price_per_kg if isinstance(price_per_kg, float) else None,
            pickup_location=pickup_text,
        )
        pricing_lines: list[str] = []
        if price_reference is not None and price_reference.mandi_modal_price_per_kg is not None:
            pricing_lines.append(
                f'- Mandi reference: Rs {price_reference.mandi_modal_price_per_kg}/kg'
                if not self._is_hindi(profile)
                else f'- मंडी रेफरेंस: Rs {price_reference.mandi_modal_price_per_kg}/किलो'
            )
            if price_reference.suggested_min_price_per_kg is not None and price_reference.suggested_max_price_per_kg is not None:
                pricing_lines.append(
                    f'- Suggested range: Rs {price_reference.suggested_min_price_per_kg}-Rs {price_reference.suggested_max_price_per_kg}/kg'
                    if not self._is_hindi(profile)
                    else f'- सुझाई गई रेंज: Rs {price_reference.suggested_min_price_per_kg}-Rs {price_reference.suggested_max_price_per_kg}/किलो'
                )
        pricing_block = f"\n{chr(10).join(pricing_lines)}" if pricing_lines else ''
        if self._is_hindi(profile):
            return (
                'लाइव करने से पहले इस लिस्टिंग को देखें:\n'
                f'- प्रोडक्ट: {product_name}\n'
                f'- मात्रा: {quantity_text}\n'
                f'- कीमत: {price_text}\n'
                f'- पिकअप: {pickup_text}\n\n'
                'इसे लाइव करें या बदलें?'
            )
        return (
            'Review this listing before it goes live:\n'
            f'- Product: {product_name}\n'
            f'- Quantity: {quantity_text}\n'
            f'- Price: {price_text}\n'
            f'- Pickup: {pickup_text}'
            f'{pricing_block}\n\n'
            'Make it live or edit it?'
        )

    def _listing_price_reference(
        self,
        *,
        product_name: str,
        quality_grade: str | None,
        seller_price_per_kg: float | None,
        pickup_location: str | None,
    ) -> Any | None:
        try:
            return self.marketplace.suggest_price(PricingSuggestionIn(
                product_name=product_name,
                quality_grade=quality_grade,
                seller_price_per_kg=seller_price_per_kg,
                pickup_location=pickup_location,
            ))
        except Exception:
            return None

    def _handle_listing_confirmation(
        self,
        *,
        profile: SellerProfile,
        session: SellerSession,
        action: str,
        raw_text: str,
    ) -> dict[str, Any]:
        if action in {LISTING_ACTION_CONFIRM_LIVE, 'live', 'make live', 'confirm', 'yes', 'ok', 'लाइव', 'हाँ', 'हां', 'ठीक'}:
            draft_message = (session.draft_message or '').strip()
            if not draft_message:
                self._clear_session(profile.seller_id)
                return self._send_text(profile, self._copy(profile, 'listing_prompt_short'), handled='seller_listing_retry')
            return self._create_listing(
                profile=profile,
                message_text=draft_message,
                image_url=str(session.draft_image_url) if session.draft_image_url else None,
                quality_assessment=self._session_quality_assessment(session),
                image_bytes=None,
                image_mime_type=None,
            )

        if action in {LISTING_ACTION_EDIT, 'edit', 'change', 'correct', 'no', 'बदलें', 'बदलो', 'सुधारो', 'नहीं'}:
            self._save_session(
                profile.seller_id,
                'awaiting_listing_message',
                draft_message=session.draft_message,
                quality_assessment=self._session_quality_assessment(session),
                draft_capture_mode=session.draft_capture_mode or 'voice_note',
                draft_image_url=str(session.draft_image_url) if session.draft_image_url else None,
            )
            return self._send_text(
                profile,
                (
                    'सही की गई लिस्टिंग भेजें, या सिर्फ वही फ़ील्ड भेजें जिसे बदलना है। उदाहरण: पिकअप नेहरू प्लेस, 20 किलो, या 30 रुपये किलो।'
                    if self._is_hindi(profile)
                    else 'Send the corrected listing, or just the field to change. Example: pickup Nehru Place, 20 kilo, or 30 rupees kilo.'
                ),
                handled='seller_listing_edit_prompt',
            )

        corrected_text = raw_text.strip()
        if corrected_text:
            corrected_text = self._merge_listing_correction(session.draft_message or '', corrected_text)
            return self._prompt_for_listing_confirmation(
                profile=profile,
                draft_message=corrected_text,
                quality_assessment=self._session_quality_assessment(session),
                capture_mode=session.draft_capture_mode or 'voice_note',
                draft_image_url=str(session.draft_image_url) if session.draft_image_url else None,
            )

        return self._prompt_for_listing_confirmation(
            profile=profile,
            draft_message=session.draft_message or '',
            quality_assessment=self._session_quality_assessment(session),
            capture_mode=session.draft_capture_mode or 'voice_note',
            draft_image_url=str(session.draft_image_url) if session.draft_image_url else None,
        )

    def _merge_listing_correction(self, draft_message: str, correction_text: str) -> str:
        correction = correction_text.strip()
        if not correction:
            return draft_message.strip()

        base_signals = self._listing_signals(draft_message)
        correction_signals = self._listing_signals(correction)

        product_name = correction_signals.get('product_name') or base_signals.get('product_name')
        quantity_kg = correction_signals.get('quantity_kg') or base_signals.get('quantity_kg')
        price_per_kg = correction_signals.get('price_per_kg') or base_signals.get('price_per_kg')

        pickup_location = correction_signals.get('pickup_location')
        correction_has_structured_detail = bool(
            correction_signals.get('product_name')
            or correction_signals.get('quantity_kg')
            or correction_signals.get('price_per_kg')
            or (pickup_location and pickup_location != DEFAULT_PICKUP_LOCATION)
        )
        if not correction_has_structured_detail:
            pickup_location = self._format_freeform_pickup(correction)
        if not pickup_location or pickup_location == DEFAULT_PICKUP_LOCATION:
            pickup_location = base_signals.get('pickup_location')
        if not pickup_location or pickup_location == DEFAULT_PICKUP_LOCATION:
            pickup_location = None

        if product_name and quantity_kg is not None and price_per_kg is not None:
            parts = [
                f'{quantity_kg:g} kilo {product_name}',
                f'{price_per_kg:g} rupees kilo',
            ]
            if pickup_location:
                parts.append(f'{pickup_location} pickup')
            return ', '.join(parts)

        return ' '.join(part for part in [draft_message.strip(), correction] if part).strip()

    def _format_freeform_pickup(self, value: str) -> str | None:
        cleaned = re.sub(r'\s+', ' ', value.strip(' ,.-')).strip()
        if not cleaned:
            return None
        if re.search(r'[a-zA-Z]', cleaned):
            return ' '.join(part.capitalize() for part in cleaned.split())
        return cleaned

    def _listing_fingerprint(self, seller_id: str, message_text: str) -> str:
        normalized = re.sub(r'\s+', ' ', message_text.strip().lower())
        if not normalized:
            return ''
        return hashlib.sha256(f'{seller_id}|{normalized}'.encode('utf-8')).hexdigest()

    def _response_fingerprint(self, seller_id: str, response_key: str) -> str:
        normalized = re.sub(r'\s+', ' ', response_key.strip().lower())
        if not normalized:
            return ''
        return hashlib.sha256(f'{seller_id}|response|{normalized}'.encode('utf-8')).hexdigest()

    def _claim_response_fingerprint(self, seller_id: str, response_key: str, *, window_seconds: int) -> bool:
        fingerprint = self._response_fingerprint(seller_id, response_key)
        if not fingerprint:
            return True
        claim = getattr(self.store, 'claim_whatsapp_message_fingerprint', None)
        if not callable(claim):
            return True
        return bool(claim(fingerprint, window_seconds=window_seconds))

    def _has_listing_signal(self, message_text: str) -> bool:
        extractor = getattr(self.marketplace, 'extractor', None)
        if extractor is not None and hasattr(extractor, 'has_listing_signal'):
            return bool(extractor.has_listing_signal(message_text))

        normalized = self._normalize_text(message_text)
        has_quantity = re.search(r'\d+(?:\.\d+)?\s*(?:kg|kgs|kilo|kilogram)', normalized) is not None
        has_price = re.search(r'(?:rs|rupees|rupay|rupaye)', normalized) is not None
        return has_quantity and has_price

    def _has_ledger_signal(self, message_text: str) -> bool:
        extractor = getattr(self.marketplace, 'extractor', None)
        if extractor is not None and hasattr(extractor, 'has_ledger_signal'):
            return bool(extractor.has_ledger_signal(message_text))

        normalized = self._normalize_text(message_text)
        return 'owes' in normalized or 'khata' in normalized or 'paid' in normalized

    def _format_ledger_confirmation(self, profile: SellerProfile, entry: LedgerEntry) -> str:
        if entry.entry_kind == 'payment':
            if self._is_hindi(profile):
                return (
                    f'खाता अपडेट हो गया। {entry.buyer_name} से Rs {entry.amount_paid:g} भुगतान दर्ज किया गया। '
                    'KHATA लिखकर पूरा बैलेंस देखें।'
                )
            return (
                f'Khata updated. Recorded Rs {entry.amount_paid:g} payment from {entry.buyer_name}. '
                'Reply KHATA to see the full balance.'
            )

        if self._is_hindi(profile):
            return (
                f'खाता अपडेट हो गया। {entry.buyer_name}, कुल Rs {self._format_number(entry.total_amount)}'
                f', मिला Rs {entry.amount_paid:g}, बाकी Rs {entry.amount_due:g}। KHATA लिखकर पूरा हिसाब देखें।'
            )
        return (
            f'Khata updated. {entry.buyer_name}: total Rs {self._format_number(entry.total_amount)}, '
            f'paid Rs {entry.amount_paid:g}, due Rs {entry.amount_due:g}. Reply KHATA to review the ledger.'
        )

    def _format_number(self, value: float | None) -> str:
        return f'{value:g}' if value is not None else '0'

    def _record_ledger_entry(
        self,
        *,
        profile: SellerProfile,
        message_text: str,
        capture_mode: LedgerCaptureMode,
    ) -> dict[str, Any]:
        entry = self.marketplace.record_ledger_entry_from_message(
            seller_id=profile.seller_id,
            message_text=message_text,
            source_channel='whatsapp',
            capture_mode=capture_mode,
        )
        if entry is None:
            retry_text = (
                'I could not understand that khata note. Try: Raju bought 10 kg tomatoes for Rs 250 and still owes Rs 50.'
                if not self._is_hindi(profile)
                else 'यह खाता नोट समझ नहीं आया। ऐसे भेजें: राजू ने 10 किलो टमाटर 250 रुपये में लिया, 50 रुपये बाकी हैं।'
            )
            return self._send_text(profile, retry_text, handled='seller_ledger_retry')
        return self._send_text(profile, self._format_ledger_confirmation(profile, entry), handled='seller_ledger_recorded')

    def _create_listing(
        self,
        *,
        profile: SellerProfile,
        message_text: str,
        image_url: str | None,
        quality_assessment: ProduceQualityAssessment | None,
        image_bytes: bytes | None,
        image_mime_type: str | None,
    ) -> dict[str, Any]:
        fingerprint = self._listing_fingerprint(profile.seller_id, message_text)
        if fingerprint and not self.store.claim_whatsapp_message_fingerprint(
            fingerprint,
            window_seconds=FINGERPRINT_WINDOW_SECONDS,
        ):
            self.whatsapp.send_text_message(to=profile.seller_id, body=self._copy(profile, 'duplicate_listing'))
            return {'ok': True, 'ignored': True, 'reason': 'duplicate_text_fingerprint'}

        try:
            listing = self.marketplace.create_listing_from_message(
                seller_id=profile.seller_id,
                seller_name=profile.seller_name,
                message_text=message_text,
                image_url=image_url,
                source_channel='whatsapp',
                default_pickup_location=profile.default_pickup_location,
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                quality_assessment=quality_assessment,
            )
        except Exception:
            if fingerprint:
                self.store.release_whatsapp_message_fingerprint(fingerprint)
            raise

        if fingerprint:
            self.store.mark_whatsapp_message_fingerprint_processed(fingerprint)
        self._clear_session(profile.seller_id)
        return {'ok': True, 'handled': 'listing_created', 'listing': listing}

    def _format_ledger_text(self, profile: SellerProfile) -> str:
        ledger = self.marketplace.build_seller_ledger(profile.seller_id)
        if ledger is None or ledger.summary.total_entries == 0:
            return self._copy(profile, 'ledger_empty')

        if self._is_hindi(profile):
            body_lines = [
                'खाता सारांश',
                f'- कुल एंट्री: {ledger.summary.total_entries}',
                f'- बाकी रकम: Rs {self._format_number(ledger.summary.total_outstanding_amount)}',
                f'- मिली रकम: Rs {self._format_number(ledger.summary.total_collected_amount)}',
                f'- बाकी वाले खरीदार: {ledger.summary.buyers_with_balance}',
                '- हाल की एंट्री:',
            ]
            for entry in ledger.summary.recent_entries:
                if entry.entry_kind == 'payment':
                    body_lines.append(f'- {entry.buyer_name}: भुगतान Rs {entry.amount_paid:g}')
                else:
                    body_lines.append(
                        f'- {entry.buyer_name}: {entry.product_name or "बिक्री"}, कुल Rs {self._format_number(entry.total_amount)}, बाकी Rs {entry.amount_due:g}'
                    )
            return '\n'.join(body_lines)

        body_lines = [
            'Khata summary',
            f'- Total entries: {ledger.summary.total_entries}',
            f'- Outstanding: Rs {self._format_number(ledger.summary.total_outstanding_amount)}',
            f'- Collected: Rs {self._format_number(ledger.summary.total_collected_amount)}',
            f'- Buyers with dues: {ledger.summary.buyers_with_balance}',
            '- Recent entries:',
        ]
        for entry in ledger.summary.recent_entries:
            if entry.entry_kind == 'payment':
                body_lines.append(f'- {entry.buyer_name}: payment Rs {entry.amount_paid:g}')
            else:
                body_lines.append(
                    f'- {entry.buyer_name}: {entry.product_name or "sale"}, total Rs {self._format_number(entry.total_amount)}, due Rs {entry.amount_due:g}'
                )
        return '\n'.join(body_lines)

    def _format_dashboard_text(self, profile: SellerProfile, dashboard: SellerDashboard) -> str:
        if dashboard.live_listings_count == 0 and dashboard.total_customers == 0 and dashboard.ledger_entries_count == 0:
            return self._copy(profile, 'dashboard_empty')
        if self._is_hindi(profile):
            return (
                f'विक्रेता डैशबोर्ड\n'
                f'- स्टोर: {dashboard.store_name or profile.store_name or profile.seller_name}\n'
                f'- डिफॉल्ट पिकअप: {dashboard.default_pickup_location or DEFAULT_PICKUP_LOCATION}\n'
                f'- लाइव लिस्टिंग: {dashboard.live_listings_count}\n'
                f'- उपलब्ध स्टॉक: {dashboard.total_available_kg} किलो\n'
                f'- आज बिका: {dashboard.sold_today_kg} किलो\n'
                f'- आज की कमाई: Rs {dashboard.sold_today_revenue}\n'
                f'- कुल ग्राहक: {dashboard.total_customers}\n'
                f'- दोबारा खरीदने वाले ग्राहक: {dashboard.repeat_customers}\n'
                f'- लंबित ऑर्डर: {dashboard.pending_orders}\n'
                f'- खाता एंट्री: {dashboard.ledger_entries_count}\n'
                f'- बाकी रकम: Rs {self._format_number(dashboard.ledger_outstanding_amount)}'
            )
        return (
            f'Seller dashboard\n'
            f'- Store: {dashboard.store_name or profile.store_name or profile.seller_name}\n'
            f'- Default pickup: {dashboard.default_pickup_location or DEFAULT_PICKUP_LOCATION}\n'
            f'- Live listings: {dashboard.live_listings_count}\n'
            f'- Stock available: {dashboard.total_available_kg} kg\n'
            f'- Sold today: {dashboard.sold_today_kg} kg\n'
            f'- Revenue today: Rs {dashboard.sold_today_revenue}\n'
            f'- Total customers: {dashboard.total_customers}\n'
            f'- Repeat customers: {dashboard.repeat_customers}\n'
            f'- Pending orders: {dashboard.pending_orders}\n'
            f'- Khata entries: {dashboard.ledger_entries_count}\n'
            f'- Outstanding dues: Rs {self._format_number(dashboard.ledger_outstanding_amount)}'
        )

    def _send_dashboard(self, profile: SellerProfile) -> dict[str, Any]:
        dashboard = self.marketplace.build_seller_dashboard(profile.seller_id)
        if dashboard is None:
            return self._send_text(profile, self._copy(profile, 'dashboard_empty'), handled='seller_dashboard')
        return self._send_text(profile, self._format_dashboard_text(profile, dashboard), handled='seller_dashboard')

    def _send_ledger(self, profile: SellerProfile) -> dict[str, Any]:
        return self._send_text(profile, self._format_ledger_text(profile), handled='seller_ledger')

    def _send_demand_pools(self, profile: SellerProfile) -> dict[str, Any]:
        pools = self.marketplace.build_demand_pools()
        if not pools:
            body = (
                'अभी कोई pooled buyer demand नहीं है। Buyer demand आते ही bulk मौके यहाँ दिखेंगे।'
                if self._is_hindi(profile)
                else 'There are no pooled buyer demand opportunities right now. Bulk demand will appear here as buyers search.'
            )
            return self._send_text(profile, body, handled='seller_demand_pools')

        body_lines = ['स्मार्ट डिमांड पूल:'] if self._is_hindi(profile) else ['Smart demand pools:']
        for pool in pools[:3]:
            avg_price = (
                f'औसत कीमत Rs {pool.average_max_price_per_kg}/किलो'
                if self._is_hindi(profile) and pool.average_max_price_per_kg is not None
                else f'avg cap Rs {pool.average_max_price_per_kg}/kg'
                if pool.average_max_price_per_kg is not None
                else ('खुली कीमत' if self._is_hindi(profile) else 'open price')
            )
            locations = ', '.join(pool.delivery_locations[:2]) if pool.delivery_locations else ('लचीला' if self._is_hindi(profile) else 'flexible')
            needed_by = ', '.join(pool.needed_by_labels[:2]) if pool.needed_by_labels else ('कोई भी समय' if self._is_hindi(profile) else 'open timing')
            if self._is_hindi(profile):
                body_lines.append(
                    f'- {pool.product_name}: {pool.total_quantity_kg:g} किलो, {pool.unique_buyer_count} खरीदार, {avg_price}, स्थान {locations}, चाहिए {needed_by}'
                )
            else:
                body_lines.append(
                    f'- {pool.product_name}: {pool.total_quantity_kg:g} kg, {pool.unique_buyer_count} buyers, {avg_price}, locations {locations}, needed by {needed_by}'
                )

        body_lines.append(
            'मैचिंग लिस्टिंग बनाने के लिए NEW भेजें।'
            if self._is_hindi(profile)
            else 'Reply NEW to create a matching listing.'
        )
        return self._send_text(profile, '\n'.join(body_lines), handled='seller_demand_pools')

    def _send_live_listings(self, profile: SellerProfile) -> dict[str, Any]:
        dashboard = self.marketplace.build_seller_dashboard(profile.seller_id)
        if dashboard is None or not dashboard.recent_listings:
            return self._send_text(profile, self._copy(profile, 'listings_empty'), handled='seller_listings')
        body_lines = ['आपकी लाइव लिस्टिंग:'] if self._is_hindi(profile) else ['Your live listings:']
        for index, item in enumerate(dashboard.recent_listings, start=1):
            quality_label = item.quality_status.replace('_', ' ').title()
            verified_label = 'BolBazaar Verified' if item.verified_by_bolbazaar else 'Unverified'
            grade_label = f'Grade {item.quality_grade}' if item.quality_grade else 'Grade pending'
            if self._is_hindi(profile):
                body_lines.append(
                    f'- {item.product_name}: {item.available_kg} किलो, Rs {item.price_per_kg}/किलो, पिकअप {item.pickup_location}'
                )
            else:
                body_lines.append(
                    f'- {index}. {item.product_name}, {item.available_kg} kg at Rs {item.price_per_kg}/kg, '
                    f'pickup {item.pickup_location}, quality {quality_label}, {grade_label}, {verified_label}'
                )
        return self._send_text(profile, '\n'.join(body_lines), handled='seller_listings')

    def _send_orders(self, profile: SellerProfile) -> dict[str, Any]:
        recent_orders = self._recent_orders(profile.seller_id)
        if not recent_orders:
            return self._send_text(profile, self._copy(profile, 'orders_empty'), handled='seller_orders')

        body_lines = ['आपके हाल के ऑर्डर:'] if self._is_hindi(profile) else ['Your recent orders:']
        for index, order in enumerate(recent_orders, start=1):
            quantity = f'{order.quantity_kg:g}'
            product_name = self._order_product_name(order)
            status = order.status.upper()
            if self._is_hindi(profile):
                line = f'- {status}: {quantity} किलो, {order.buyer_name}, पिकअप {order.pickup_time}'
                if order.status == 'pending':
                    line += '। जवाब दें: YES या NO'
            else:
                line = f'- {status}: {order.id}, {quantity} kg {product_name}, {order.buyer_name}, pickup {order.pickup_time}'
                if order.status == 'pending':
                    line += f'. Reply YES {index}, NO {index}, ACCEPT ORDER {order.id}, or REJECT ORDER {order.id}'
            line = f'- {index}. {line[2:]}' if line.startswith('- ') else f'- {index}. {line}'
            body_lines.append(line)

        pending_action_rows: list[dict[str, str]] = []
        for index, order in enumerate(recent_orders, start=1):
            if order.status != 'pending':
                continue
            quantity = f'{order.quantity_kg:g}'
            product_name = self._order_product_name(order)
            description = f'{quantity} kg {product_name}, {order.buyer_name}, pickup {order.pickup_time}'
            pending_action_rows.extend([
                {'id': f'order_accept:{order.id}', 'title': f'Accept {index}', 'description': description},
                {'id': f'order_reject:{order.id}', 'title': f'Reject {index}', 'description': description},
            ])

        if pending_action_rows:
            result = self.whatsapp.send_list_message(
                to=profile.seller_id,
                body='\n'.join(body_lines),
                button_text='Manage orders',
                sections=[
                    {
                        'title': 'Pending orders',
                        'rows': pending_action_rows,
                    }
                ],
            )
            if result.get('sent'):
                return {'ok': True, 'handled': 'seller_orders'}

        return self._send_text(profile, '\n'.join(body_lines), handled='seller_orders')

    def _send_customers(self, profile: SellerProfile) -> dict[str, Any]:
        dashboard = self.marketplace.build_seller_dashboard(profile.seller_id)
        if dashboard is None or not dashboard.recent_customers:
            return self._send_text(profile, self._copy(profile, 'customers_empty'), handled='seller_customers')
        title = 'हाल के ग्राहक:\n' if self._is_hindi(profile) else 'Recent customers:\n'
        body = title + '\n'.join(f'- {name}' for name in dashboard.recent_customers)
        return self._send_text(profile, body, handled='seller_customers')

    def _send_profile(self, profile: SellerProfile) -> dict[str, Any]:
        verification_label = VERIFICATION_METHOD_TITLES.get(profile.verification_method or '', '-')
        seller_type_label = SELLER_TYPE_TITLES.get(profile.seller_type or '', '-')
        proof_status = 'On file' if profile.verification_proof_url else 'Missing'
        if self._is_hindi(profile):
            seller_type_label = {
                'farmer': 'किसान',
                'aggregator': 'एग्रीगेटर',
                'fpo': 'FPO',
                'trader': 'ट्रेडर',
            }.get(profile.seller_type or '', '-')
            verification_label = {
                'farmer_registry': 'किसान रजिस्ट्री',
                'pm_kisan': 'PM-KISAN',
                'enam': 'eNAM',
                'fpo_certificate': 'FPO प्रमाणपत्र',
                'fssai': 'FSSAI',
                'govt_id': 'सरकारी ID',
                'other': 'अन्य प्रमाण',
            }.get(profile.verification_method or '', '-')
            proof_status = 'मौजूद' if profile.verification_proof_url else 'नहीं है'
            body = (
                f"{self._copy(profile, 'profile_title')}\n"
                f'- विक्रेता नाम: {profile.seller_name}\n'
                f'- स्टोर नाम: {profile.store_name or "-"}\n'
                f'- विक्रेता प्रकार: {seller_type_label}\n'
                f'- भाषा: {profile.preferred_language}\n'
                f'- डिफॉल्ट पिकअप: {profile.default_pickup_location or DEFAULT_PICKUP_LOCATION}\n'
                f'- सत्यापन: {profile.verification_status} via {verification_label}\n'
                f'- सत्यापन नंबर: {profile.verification_number or "-"}\n'
                f'- सत्यापन प्रमाण: {proof_status}\n'
                'जानकारी अपडेट करने के लिए KHATA, NAME, STORE, LANGUAGE, TYPE, VERIFY METHOD, VERIFY ID, VERIFY PROOF या LOCATION लिखें।'
            )
            return self._send_text(profile, body, handled='seller_profile')
        body = (
            f"{self._copy(profile, 'profile_title')}\n"
            f'- Seller name: {profile.seller_name}\n'
            f'- Store name: {profile.store_name or "-"}\n'
            f'- Seller type: {seller_type_label}\n'
            f'- Language: {profile.preferred_language}\n'
            f'- Default pickup: {profile.default_pickup_location or DEFAULT_PICKUP_LOCATION}\n'
            f'- Verification: {profile.verification_status} via {verification_label}\n'
            f'- Verification number: {profile.verification_number or "-"}\n'
            f'- Verification proof: {proof_status}\n'
            'Reply KHATA, NAME, STORE, LANGUAGE, TYPE, VERIFY METHOD, VERIFY ID, VERIFY PROOF, or LOCATION to manage details.'
        )
        return self._send_text(profile, body, handled='seller_profile')
