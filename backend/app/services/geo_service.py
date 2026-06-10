from __future__ import annotations

import math
from typing import Any

import httpx

from app.config import get_settings
from app.schemas import DeliveryFeeBreakdown


class GeoService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def geocode(self, location: str) -> dict[str, Any] | None:
        if not self.settings.maps_api_key or not location.strip():
            return None
        try:
            response = httpx.get(
                'https://maps.googleapis.com/maps/api/geocode/json',
                params={'address': location, 'key': self.settings.maps_api_key},
                timeout=15.0,
            )
            response.raise_for_status()
            payload = response.json()
            results = payload.get('results', [])
            if not results:
                return None
            top = results[0]
            geom = top.get('geometry', {}).get('location', {})
            return {
                'pickup_location': top.get('formatted_address', location),
                'latitude': geom.get('lat'),
                'longitude': geom.get('lng'),
                'place_id': top.get('place_id'),
            }
        except httpx.HTTPError:
            return None

    def haversine_km(self, lat1, lng1, lat2, lng2):
        if None in (lat1, lng1, lat2, lng2):
            return None
        r = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
        a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        return round(2 * r * math.asin(math.sqrt(a)), 2)

    def estimate_delivery_fee(self, distance_km):
        from app.config import get_settings
        s = get_settings()
        if distance_km is None:
            return round(s.delivery_base_fee, 2)
        billable = max(distance_km - s.delivery_free_radius_km, 0.0)
        return round(s.delivery_base_fee + billable * s.delivery_per_km_fee, 2)

    def google_distance_km(self, origin: str, destination: str) -> float | None:
        if not self.settings.maps_api_key or not origin.strip() or not destination.strip():
            return None
        try:
            response = httpx.get(
                'https://maps.googleapis.com/maps/api/distancematrix/json',
                params={
                    'origins': origin,
                    'destinations': destination,
                    'units': 'metric',
                    'key': self.settings.maps_api_key,
                },
                timeout=15.0,
            )
            response.raise_for_status()
            payload = response.json()
            rows = payload.get('rows') or []
            if not rows:
                return None
            elements = rows[0].get('elements') or []
            if not elements or elements[0].get('status') != 'OK':
                return None
            meters = elements[0].get('distance', {}).get('value')
            if meters is None:
                return None
            return round(float(meters) / 1000.0, 2)
        except httpx.HTTPError:
            return None

    def resolve_distance(
        self,
        *,
        origin_address: str,
        destination_address: str,
        origin_lat: float | None = None,
        origin_lng: float | None = None,
        destination_lat: float | None = None,
        destination_lng: float | None = None,
    ) -> tuple[float | None, str]:
        google_distance = self.google_distance_km(origin_address, destination_address)
        if google_distance is not None:
            return google_distance, 'google_maps'
        haversine_distance = self.haversine_km(origin_lat, origin_lng, destination_lat, destination_lng)
        if haversine_distance is not None:
            return haversine_distance, 'haversine'
        return None, 'unavailable'

    def estimate_delivery_breakdown(self, *, quantity_kg: float, distance_km: float | None, distance_source: str) -> DeliveryFeeBreakdown:
        settings = self.settings
        pricing_notes: list[str] = []
        if distance_source != 'google_maps':
            pricing_notes.append('Estimated pricing shown because live route distance was unavailable.')
        if distance_km is None:
            pricing_notes.append('Price data unavailable for route distance; using minimum delivery estimate.')

        billable_distance = max((distance_km or 0.0) - settings.delivery_free_radius_km, 0.0)
        extra_weight_kg = max(quantity_kg - settings.delivery_weight_included_kg, 0.0)
        base_fee = settings.delivery_base_fee
        distance_fee = billable_distance * settings.delivery_per_km_fee
        weight_fee = extra_weight_kg * settings.delivery_per_extra_kg_fee
        surged_total = (base_fee + distance_fee + weight_fee) * settings.delivery_surge_multiplier
        total_delivery_fee = min(max(surged_total, settings.delivery_min_fee), settings.delivery_max_fee)
        surge_fee = max(surged_total - (base_fee + distance_fee + weight_fee), 0.0)
        total_delivery_fee = round(total_delivery_fee)

        return DeliveryFeeBreakdown(
            distance_km=distance_km,
            distance_source=distance_source,  # type: ignore[arg-type]
            base_fee=round(base_fee, 2),
            distance_fee=round(distance_fee, 2),
            weight_fee=round(weight_fee, 2),
            surge_fee=round(surge_fee, 2),
            total_delivery_fee=total_delivery_fee,
            currency='INR',
            fee_label='Estimated delivery fee' if distance_source != 'google_maps' else 'Delivery fee',
            pricing_notes=pricing_notes,
        )
