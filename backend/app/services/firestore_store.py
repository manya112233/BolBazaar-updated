from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.google_clients import GoogleClients
from app.schemas import BuyerDemandEvent, LedgerEntry, Listing, Order, OtpRequestRecord, SellerInsight, SellerProfile, SellerSession

try:
    from google.api_core.exceptions import AlreadyExists
except ImportError:  # pragma: no cover - dependency is present in runtime when Firestore is enabled
    AlreadyExists = Exception


class FirestoreStore:
    def __init__(self) -> None:
        client = GoogleClients().firestore()
        if client is None:
            raise RuntimeError('google-cloud-firestore is not installed or could not be initialized')

        self.db = client
        self.listings_collection = self.db.collection('listings')
        self.orders_collection = self.db.collection('orders')
        self.ledger_entries_collection = self.db.collection('ledger_entries')
        self.buyer_searches_collection = self.db.collection('buyer_searches')
        self.meta_collection = self.db.collection('meta')
        self.insights_collection = self.db.collection('insights')
        self.seller_profiles_collection = self.db.collection('seller_profiles')
        self.seller_sessions_collection = self.db.collection('seller_sessions')
        self.otp_requests_collection = self.db.collection('otp_requests')
        self.demand_alert_fingerprints_collection = self.db.collection('demand_alert_fingerprints')
        self.whatsapp_messages_collection = self.db.collection('whatsapp_message_states')
        self.whatsapp_message_fingerprints_collection = self.db.collection('whatsapp_message_fingerprints')
        self._validate_connection()

    def _validate_connection(self) -> None:
        # Force a real API call during initialization so disabled Firestore projects
        # fall back to the local store instead of crashing later inside a webhook.
        self.meta_collection.document('__connection_probe__').get()

    def reset(self) -> None:
        for collection in [
            self.listings_collection,
            self.orders_collection,
            self.ledger_entries_collection,
            self.buyer_searches_collection,
            self.insights_collection,
            self.seller_profiles_collection,
            self.seller_sessions_collection,
            self.otp_requests_collection,
            self.demand_alert_fingerprints_collection,
            self.whatsapp_messages_collection,
            self.whatsapp_message_fingerprints_collection,
        ]:
            for doc in collection.stream():
                doc.reference.delete()
        self.meta_collection.document('notifications').set({'items': []})

    def list_listings(self) -> list[Listing]:
        docs = self.listings_collection.stream()
        return [Listing.model_validate(doc.to_dict()) for doc in docs]

    def save_listing(self, listing: Listing) -> Listing:
        self.listings_collection.document(listing.id).set(listing.model_dump(mode='json'))
        return listing

    def get_listing(self, listing_id: str) -> Listing | None:
        doc = self.listings_collection.document(listing_id).get()
        if not doc.exists:
            return None
        return Listing.model_validate(doc.to_dict())

    def list_orders(self) -> list[Order]:
        docs = self.orders_collection.stream()
        return [Order.model_validate(doc.to_dict()) for doc in docs]

    def save_order(self, order: Order) -> Order:
        self.orders_collection.document(order.id).set(order.model_dump(mode='json'))
        return order

    def get_order(self, order_id: str) -> Order | None:
        doc = self.orders_collection.document(order_id).get()
        if not doc.exists:
            return None
        return Order.model_validate(doc.to_dict())

    def list_ledger_entries(self) -> list[LedgerEntry]:
        docs = self.ledger_entries_collection.stream()
        return [LedgerEntry.model_validate(doc.to_dict()) for doc in docs]

    def save_ledger_entry(self, entry: LedgerEntry) -> LedgerEntry:
        self.ledger_entries_collection.document(entry.id).set(entry.model_dump(mode='json'))
        return entry

    def add_notification(self, payload: dict[str, Any]) -> None:
        ref = self.meta_collection.document('notifications')
        doc = ref.get()
        items = [] if not doc.exists else doc.to_dict().get('items', [])
        items.append(payload)
        ref.set({'items': items})

    def list_notifications(self) -> list[dict[str, Any]]:
        doc = self.meta_collection.document('notifications').get()
        if not doc.exists:
            return []
        return doc.to_dict().get('items', [])

    def list_buyer_search_events(
        self,
        *,
        since: datetime | None = None,
        detected_product_name: str | None = None,
    ) -> list[BuyerDemandEvent]:
        docs = self.buyer_searches_collection.stream()
        items = [BuyerDemandEvent.model_validate(doc.to_dict()) for doc in docs]

        if since is not None:
            items = [item for item in items if item.created_at >= since]

        if detected_product_name:
            target = detected_product_name.strip().lower()
            items = [
                item
                for item in items
                if item.detected_product_name and item.detected_product_name.strip().lower() == target
            ]

        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def save_buyer_search_event(self, event: BuyerDemandEvent) -> BuyerDemandEvent:
        self.buyer_searches_collection.document(event.id).set(event.model_dump(mode='json'))
        return event

    def save_insight(self, insight: SellerInsight) -> SellerInsight:
        self.insights_collection.document(insight.seller_id).set(insight.model_dump(mode='json'))
        return insight

    def get_insight(self, seller_id: str) -> SellerInsight | None:
        doc = self.insights_collection.document(seller_id).get()
        if not doc.exists:
            return None
        return SellerInsight.model_validate(doc.to_dict())

    def list_seller_profiles(self) -> list[SellerProfile]:
        docs = self.seller_profiles_collection.stream()
        return [SellerProfile.model_validate(doc.to_dict()) for doc in docs]

    def get_seller_profile(self, seller_id: str) -> SellerProfile | None:
        doc = self.seller_profiles_collection.document(seller_id).get()
        if not doc.exists:
            return None
        return SellerProfile.model_validate(doc.to_dict())

    def save_seller_profile(self, profile: SellerProfile) -> SellerProfile:
        self.seller_profiles_collection.document(profile.seller_id).set(profile.model_dump(mode='json'))
        return profile

    def get_seller_session(self, seller_id: str) -> SellerSession | None:
        doc = self.seller_sessions_collection.document(seller_id).get()
        if not doc.exists:
            return None
        return SellerSession.model_validate(doc.to_dict())

    def save_seller_session(self, session: SellerSession) -> SellerSession:
        self.seller_sessions_collection.document(session.seller_id).set(session.model_dump(mode='json'))
        return session

    def clear_seller_session(self, seller_id: str) -> None:
        self.seller_sessions_collection.document(seller_id).delete()

    def list_otp_requests(self) -> list[OtpRequestRecord]:
        docs = self.otp_requests_collection.stream()
        return [OtpRequestRecord.model_validate(doc.to_dict()) for doc in docs]

    def get_otp_request(self, request_id: str) -> OtpRequestRecord | None:
        doc = self.otp_requests_collection.document(request_id).get()
        if not doc.exists:
            return None
        return OtpRequestRecord.model_validate(doc.to_dict())

    def save_otp_request(self, request_record: OtpRequestRecord) -> OtpRequestRecord:
        self.otp_requests_collection.document(request_record.id).set(request_record.model_dump(mode='json'))
        return request_record

    def claim_whatsapp_message(self, message_id: str) -> bool:
        if not message_id:
            return False

        ref = self.whatsapp_messages_collection.document(message_id)
        payload = {
            'status': 'processing',
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        try:
            ref.create(payload)
            return True
        except AlreadyExists:
            return False

    def has_processed_whatsapp_message(self, message_id: str) -> bool:
        if not message_id:
            return False

        doc = self.whatsapp_messages_collection.document(message_id).get()
        if not doc.exists:
            return False
        return doc.to_dict().get('status') == 'processed'

    def mark_whatsapp_message_processed(self, message_id: str) -> None:
        if not message_id:
            return

        self.whatsapp_messages_collection.document(message_id).set({
            'status': 'processed',
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

    def release_whatsapp_message_claim(self, message_id: str) -> None:
        if not message_id:
            return

        ref = self.whatsapp_messages_collection.document(message_id)
        doc = ref.get()
        if not doc.exists:
            return
        if doc.to_dict().get('status') == 'processing':
            ref.delete()

    def claim_whatsapp_message_fingerprint(self, fingerprint: str, window_seconds: int = 90) -> bool:
        if not fingerprint:
            return True

        ref = self.whatsapp_message_fingerprints_collection.document(fingerprint)
        doc = ref.get()
        now = datetime.now(timezone.utc)
        if doc.exists:
            payload = doc.to_dict()
            updated_at_raw = payload.get('updated_at')
            updated_at = None
            if updated_at_raw:
                try:
                    updated_at = datetime.fromisoformat(updated_at_raw)
                except ValueError:
                    updated_at = None
            if updated_at is not None and updated_at >= now - timedelta(seconds=window_seconds):
                return False

        ref.set({
            'status': 'processing',
            'updated_at': now.isoformat(),
        })
        return True

    def mark_whatsapp_message_fingerprint_processed(self, fingerprint: str) -> None:
        if not fingerprint:
            return

        self.whatsapp_message_fingerprints_collection.document(fingerprint).set({
            'status': 'processed',
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

    def release_whatsapp_message_fingerprint(self, fingerprint: str) -> None:
        if not fingerprint:
            return

        ref = self.whatsapp_message_fingerprints_collection.document(fingerprint)
        doc = ref.get()
        if not doc.exists:
            return
        if doc.to_dict().get('status') == 'processing':
            ref.delete()

    def claim_demand_alert_fingerprint(self, fingerprint: str, window_seconds: int = 1800) -> bool:
        if not fingerprint:
            return True

        ref = self.demand_alert_fingerprints_collection.document(fingerprint)
        doc = ref.get()
        now = datetime.now(timezone.utc)
        if doc.exists:
            payload = doc.to_dict()
            updated_at_raw = payload.get('updated_at')
            updated_at = None
            if updated_at_raw:
                try:
                    updated_at = datetime.fromisoformat(updated_at_raw)
                except ValueError:
                    updated_at = None
            if updated_at is not None and updated_at >= now - timedelta(seconds=window_seconds):
                return False

        ref.set({
            'status': 'processing',
            'updated_at': now.isoformat(),
        })
        return True

    def mark_demand_alert_fingerprint_processed(self, fingerprint: str) -> None:
        if not fingerprint:
            return

        self.demand_alert_fingerprints_collection.document(fingerprint).set({
            'status': 'processed',
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

    def release_demand_alert_fingerprint(self, fingerprint: str) -> None:
        if not fingerprint:
            return

        ref = self.demand_alert_fingerprints_collection.document(fingerprint)
        doc = ref.get()
        if not doc.exists:
            return
        if doc.to_dict().get('status') == 'processing':
            ref.delete()
