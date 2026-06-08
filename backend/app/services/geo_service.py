from __future__ import annotations

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
