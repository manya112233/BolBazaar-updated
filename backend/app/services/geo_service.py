from __future__ import annotations

import math
from typing import Any

import httpx

from app.config import get_settings


class GeoService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def geocode(self, location: str) -> dict[str, Any] | None:
        if not self.settings.maps_api_key or not location.strip():
            return None

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
