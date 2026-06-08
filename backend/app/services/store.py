# from __future__ import annotations

# import json
# from pathlib import Path
# from typing import Any

# from app.schemas import Listing, Order, SellerInsight


# class JsonStore:
#     def __init__(self, file_path: Path):
#         self.file_path = file_path
#         self.file_path.parent.mkdir(parents=True, exist_ok=True)
#         if not self.file_path.exists():
#             self._write({"listings": [], "orders": [], "notifications": [], "insights": []})

#     def _read(self) -> dict[str, Any]:
#         with self.file_path.open("r", encoding="utf-8") as f:
#             return json.load(f)

#     def _write(self, payload: dict[str, Any]) -> None:
#         with self.file_path.open("w", encoding="utf-8") as f:
#             json.dump(payload, f, indent=2, ensure_ascii=False)

#     def reset(self) -> None:
#         self._write({"listings": [], "orders": [], "notifications": [], "insights": []})

#     def list_listings(self) -> list[Listing]:
#         data = self._read()
#         return [Listing.model_validate(item) for item in data["listings"]]

#     def save_listing(self, listing: Listing) -> Listing:
#         data = self._read()
#         listings = [item for item in data["listings"] if item["id"] != listing.id]
#         listings.append(json.loads(listing.model_dump_json()))
#         data["listings"] = listings
#         self._write(data)
#         return listing

#     def get_listing(self, listing_id: str) -> Listing | None:
#         for listing in self.list_listings():
#             if listing.id == listing_id:
#                 return listing
#         return None

#     def list_orders(self) -> list[Order]:
#         data = self._read()
#         return [Order.model_validate(item) for item in data["orders"]]

#     def save_order(self, order: Order) -> Order:
#         data = self._read()
#         orders = [item for item in data["orders"] if item["id"] != order.id]
#         orders.append(json.loads(order.model_dump_json()))
#         data["orders"] = orders
#         self._write(data)
#         return order

#     def get_order(self, order_id: str) -> Order | None:
#         for order in self.list_orders():
#             if order.id == order_id:
#                 return order
#         return None

#     def add_notification(self, payload: dict[str, Any]) -> None:
#         data = self._read()
#         data["notifications"].append(payload)
#         self._write(data)

#     def list_notifications(self) -> list[dict[str, Any]]:
#         return self._read()["notifications"]

#     def save_insight(self, insight: SellerInsight) -> SellerInsight:
#         data = self._read()
#         insights = [item for item in data["insights"] if item["seller_id"] != insight.seller_id]
#         insights.append(json.loads(insight.model_dump_json()))
#         data["insights"] = insights
#         self._write(data)
#         return insight

#     def get_insight(self, seller_id: str) -> SellerInsight | None:
#         data = self._read()
#         for item in data["insights"]:
#             if item["seller_id"] == seller_id:
#                 return SellerInsight.model_validate(item)
#         return None
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from app.schemas import BuyerDemandEvent, LedgerEntry, Listing, Order, OtpRequestRecord, SellerInsight, SellerProfile, SellerSession


class JsonStore:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._lock = RLock()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._write({
                "listings": [],
                "orders": [],
                "ledger_entries": [],
                "buyer_searches": [],
                "notifications": [],
                "insights": [],
                "seller_profiles": [],
                "seller_sessions": [],
                "otp_requests": [],
                "demand_alert_fingerprints": {},
                "whatsapp_message_fingerprints": {},
                "whatsapp_message_states": {},
                "processed_whatsapp_message_ids": [],
            })

    def _read(self) -> dict[str, Any]:
        with self.file_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, payload: dict[str, Any]) -> None:
        with self.file_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def reset(self) -> None:
        with self._lock:
            self._write({
                "listings": [],
                "orders": [],
                "ledger_entries": [],
                "buyer_searches": [],
                "notifications": [],
                "insights": [],
                "seller_profiles": [],
                "seller_sessions": [],
                "otp_requests": [],
                "demand_alert_fingerprints": {},
                "whatsapp_message_fingerprints": {},
                "whatsapp_message_states": {},
                "processed_whatsapp_message_ids": [],
            })

    def list_listings(self) -> list[Listing]:
        data = self._read()
        return [Listing.model_validate(item) for item in data["listings"]]

    def save_listing(self, listing: Listing) -> Listing:
        with self._lock:
            data = self._read()
            listings = [item for item in data["listings"] if item["id"] != listing.id]
            listings.append(json.loads(listing.model_dump_json()))
            data["listings"] = listings
            self._write(data)
        return listing

    def get_listing(self, listing_id: str) -> Listing | None:
        for listing in self.list_listings():
            if listing.id == listing_id:
                return listing
        return None

    def list_orders(self) -> list[Order]:
        data = self._read()
        return [Order.model_validate(item) for item in data["orders"]]

    def save_order(self, order: Order) -> Order:
        with self._lock:
            data = self._read()
            orders = [item for item in data["orders"] if item["id"] != order.id]
            orders.append(json.loads(order.model_dump_json()))
            data["orders"] = orders
            self._write(data)
        return order

    def get_order(self, order_id: str) -> Order | None:
        for order in self.list_orders():
            if order.id == order_id:
                return order
        return None

    def list_ledger_entries(self) -> list[LedgerEntry]:
        data = self._read()
        return [LedgerEntry.model_validate(item) for item in data.get("ledger_entries", [])]

    def save_ledger_entry(self, entry: LedgerEntry) -> LedgerEntry:
        with self._lock:
            data = self._read()
            entries = [item for item in data.get("ledger_entries", []) if item["id"] != entry.id]
            entries.append(json.loads(entry.model_dump_json()))
            data["ledger_entries"] = entries
            self._write(data)
        return entry

    def add_notification(self, payload: dict[str, Any]) -> None:
        with self._lock:
            data = self._read()
            data["notifications"].append(payload)
            self._write(data)

    def list_notifications(self) -> list[dict[str, Any]]:
        return self._read()["notifications"]

    def list_buyer_search_events(
        self,
        *,
        since: datetime | None = None,
        detected_product_name: str | None = None,
    ) -> list[BuyerDemandEvent]:
        data = self._read()
        items = [BuyerDemandEvent.model_validate(item) for item in data.get("buyer_searches", [])]

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
        with self._lock:
            data = self._read()
            events = [item for item in data.get("buyer_searches", []) if item.get("id") != event.id]
            events.append(json.loads(event.model_dump_json()))
            data["buyer_searches"] = events
            self._write(data)
        return event

    def save_insight(self, insight: SellerInsight) -> SellerInsight:
        with self._lock:
            data = self._read()
            insights = [item for item in data["insights"] if item["seller_id"] != insight.seller_id]
            insights.append(json.loads(insight.model_dump_json()))
            data["insights"] = insights
            self._write(data)
        return insight

    def get_insight(self, seller_id: str) -> SellerInsight | None:
        data = self._read()
        for item in data["insights"]:
            if item["seller_id"] == seller_id:
                return SellerInsight.model_validate(item)
        return None

    def list_seller_profiles(self) -> list[SellerProfile]:
        data = self._read()
        return [SellerProfile.model_validate(item) for item in data.get("seller_profiles", [])]

    def get_seller_profile(self, seller_id: str) -> SellerProfile | None:
        for profile in self.list_seller_profiles():
            if profile.seller_id == seller_id:
                return profile
        return None

    def save_seller_profile(self, profile: SellerProfile) -> SellerProfile:
        with self._lock:
            data = self._read()
            profiles = [item for item in data.get("seller_profiles", []) if item["seller_id"] != profile.seller_id]
            profiles.append(json.loads(profile.model_dump_json()))
            data["seller_profiles"] = profiles
            self._write(data)
        return profile

    def get_seller_session(self, seller_id: str) -> SellerSession | None:
        data = self._read()
        for item in data.get("seller_sessions", []):
            if item["seller_id"] == seller_id:
                return SellerSession.model_validate(item)
        return None

    def save_seller_session(self, session: SellerSession) -> SellerSession:
        with self._lock:
            data = self._read()
            sessions = [item for item in data.get("seller_sessions", []) if item["seller_id"] != session.seller_id]
            sessions.append(json.loads(session.model_dump_json()))
            data["seller_sessions"] = sessions
            self._write(data)
        return session

    def clear_seller_session(self, seller_id: str) -> None:
        with self._lock:
            data = self._read()
            data["seller_sessions"] = [
                item for item in data.get("seller_sessions", [])
                if item["seller_id"] != seller_id
            ]
            self._write(data)

    def list_otp_requests(self) -> list[OtpRequestRecord]:
        data = self._read()
        return [OtpRequestRecord.model_validate(item) for item in data.get("otp_requests", [])]

    def get_otp_request(self, request_id: str) -> OtpRequestRecord | None:
        for item in self.list_otp_requests():
            if item.id == request_id:
                return item
        return None

    def save_otp_request(self, request_record: OtpRequestRecord) -> OtpRequestRecord:
        with self._lock:
            data = self._read()
            items = [item for item in data.get("otp_requests", []) if item["id"] != request_record.id]
            items.append(json.loads(request_record.model_dump_json()))
            data["otp_requests"] = items
            self._write(data)
        return request_record

    def _message_states(self, data: dict[str, Any]) -> dict[str, dict[str, str]]:
        raw_states = data.get("whatsapp_message_states")
        if isinstance(raw_states, dict):
            return {
                str(key): value
                for key, value in raw_states.items()
                if isinstance(value, dict)
            }

        legacy_ids = data.get("processed_whatsapp_message_ids", [])
        return {
            str(message_id): {
                "status": "processed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            for message_id in legacy_ids
            if message_id
        }

    def _message_fingerprints(self, data: dict[str, Any]) -> dict[str, dict[str, str]]:
        raw_states = data.get("whatsapp_message_fingerprints")
        if not isinstance(raw_states, dict):
            return {}
        return {
            str(key): value
            for key, value in raw_states.items()
            if isinstance(value, dict)
        }

    def _demand_alert_fingerprints(self, data: dict[str, Any]) -> dict[str, dict[str, str]]:
        raw_states = data.get("demand_alert_fingerprints")
        if not isinstance(raw_states, dict):
            return {}
        return {
            str(key): value
            for key, value in raw_states.items()
            if isinstance(value, dict)
        }

    def _parse_timestamp(self, timestamp: str | None) -> datetime | None:
        if not timestamp:
            return None
        try:
            return datetime.fromisoformat(timestamp)
        except ValueError:
            return None

    def _persist_message_states(self, data: dict[str, Any], states: dict[str, dict[str, str]]) -> None:
        data["whatsapp_message_states"] = states
        data["processed_whatsapp_message_ids"] = [
            message_id
            for message_id, item in states.items()
            if item.get("status") == "processed"
        ]

    def _persist_message_fingerprints(self, data: dict[str, Any], states: dict[str, dict[str, str]]) -> None:
        data["whatsapp_message_fingerprints"] = states

    def _persist_demand_alert_fingerprints(self, data: dict[str, Any], states: dict[str, dict[str, str]]) -> None:
        data["demand_alert_fingerprints"] = states

    def claim_whatsapp_message(self, message_id: str) -> bool:
        if not message_id:
            return False

        with self._lock:
            data = self._read()
            states = self._message_states(data)
            state = states.get(message_id, {})
            if state.get("status") in {"processing", "processed"}:
                return False

            states[message_id] = {
                "status": "processing",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._persist_message_states(data, states)
            self._write(data)
            return True

    def has_processed_whatsapp_message(self, message_id: str) -> bool:
        data = self._read()
        states = self._message_states(data)
        return states.get(message_id, {}).get("status") == "processed"

    def mark_whatsapp_message_processed(self, message_id: str) -> None:
        if not message_id:
            return

        with self._lock:
            data = self._read()
            states = self._message_states(data)
            states[message_id] = {
                "status": "processed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._persist_message_states(data, states)
            self._write(data)

    def release_whatsapp_message_claim(self, message_id: str) -> None:
        if not message_id:
            return

        with self._lock:
            data = self._read()
            states = self._message_states(data)
            state = states.get(message_id, {})
            if state.get("status") == "processing":
                states.pop(message_id, None)
                self._persist_message_states(data, states)
                self._write(data)

    def claim_whatsapp_message_fingerprint(self, fingerprint: str, window_seconds: int = 90) -> bool:
        if not fingerprint:
            return True

        now = datetime.now(timezone.utc)
        with self._lock:
            data = self._read()
            states = self._message_fingerprints(data)
            expires_before = now - timedelta(seconds=window_seconds)
            states = {
                key: value
                for key, value in states.items()
                if (self._parse_timestamp(value.get("updated_at")) or now) >= expires_before
            }

            state = states.get(fingerprint, {})
            if state.get("status") in {"processing", "processed"}:
                self._persist_message_fingerprints(data, states)
                self._write(data)
                return False

            states[fingerprint] = {
                "status": "processing",
                "updated_at": now.isoformat(),
            }
            self._persist_message_fingerprints(data, states)
            self._write(data)
            return True

    def mark_whatsapp_message_fingerprint_processed(self, fingerprint: str) -> None:
        if not fingerprint:
            return

        with self._lock:
            data = self._read()
            states = self._message_fingerprints(data)
            states[fingerprint] = {
                "status": "processed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._persist_message_fingerprints(data, states)
            self._write(data)

    def release_whatsapp_message_fingerprint(self, fingerprint: str) -> None:
        if not fingerprint:
            return

        with self._lock:
            data = self._read()
            states = self._message_fingerprints(data)
            state = states.get(fingerprint, {})
            if state.get("status") == "processing":
                states.pop(fingerprint, None)
                self._persist_message_fingerprints(data, states)
                self._write(data)

    def claim_demand_alert_fingerprint(self, fingerprint: str, window_seconds: int = 1800) -> bool:
        if not fingerprint:
            return True

        now = datetime.now(timezone.utc)
        with self._lock:
            data = self._read()
            states = self._demand_alert_fingerprints(data)
            expires_before = now - timedelta(seconds=window_seconds)
            states = {
                key: value
                for key, value in states.items()
                if (self._parse_timestamp(value.get("updated_at")) or now) >= expires_before
            }

            state = states.get(fingerprint, {})
            if state.get("status") in {"processing", "processed"}:
                self._persist_demand_alert_fingerprints(data, states)
                self._write(data)
                return False

            states[fingerprint] = {
                "status": "processing",
                "updated_at": now.isoformat(),
            }
            self._persist_demand_alert_fingerprints(data, states)
            self._write(data)
            return True

    def mark_demand_alert_fingerprint_processed(self, fingerprint: str) -> None:
        if not fingerprint:
            return

        with self._lock:
            data = self._read()
            states = self._demand_alert_fingerprints(data)
            states[fingerprint] = {
                "status": "processed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._persist_demand_alert_fingerprints(data, states)
            self._write(data)

    def release_demand_alert_fingerprint(self, fingerprint: str) -> None:
        if not fingerprint:
            return

        with self._lock:
            data = self._read()
            states = self._demand_alert_fingerprints(data)
            state = states.get(fingerprint, {})
            if state.get("status") == "processing":
                states.pop(fingerprint, None)
                self._persist_demand_alert_fingerprints(data, states)
                self._write(data)
