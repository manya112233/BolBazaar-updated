from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import get_settings
from app.schemas import MarketPriceReference
from app.services.extraction import ExtractionService


class MarketPriceService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.extractor = ExtractionService()
        self._cache: dict[str, tuple[datetime, list[MarketPriceReference]]] = {}

    def _cache_key(self, commodity: str, state: str | None, district: str | None, market: str | None) -> str:
        return '|'.join([
            commodity.strip().lower(),
            (state or '').strip().lower(),
            (district or '').strip().lower(),
            (market or '').strip().lower(),
        ])

    def _normalize_commodity(self, commodity: str) -> str:
        normalized, _ = self.extractor._normalize_detected_product(commodity)
        return normalized or commodity.strip().title()

    def _fallback_records(self, commodity: str) -> list[dict[str, Any]]:
        normalized = self._normalize_commodity(commodity)
        fallback: dict[str, dict[str, Any]] = {
            'Tomato': {'modal_price': 2800, 'min_price': 2400, 'max_price': 3200, 'state': 'Maharashtra', 'district': 'Pune', 'market': 'Pune'},
            'Onion': {'modal_price': 2400, 'min_price': 2100, 'max_price': 2750, 'state': 'Maharashtra', 'district': 'Nashik', 'market': 'Lasalgaon'},
            'Potato': {'modal_price': 2200, 'min_price': 1900, 'max_price': 2550, 'state': 'Uttar Pradesh', 'district': 'Agra', 'market': 'Agra'},
        }
        record = fallback.get(normalized, {
            'modal_price': 3000,
            'min_price': 2600,
            'max_price': 3400,
            'state': self.settings.mandi_price_default_state,
            'district': None,
            'market': self.settings.mandi_price_default_market,
        })
        return [{
            'commodity': normalized,
            'state': record['state'],
            'district': record['district'],
            'market': record['market'],
            'min_price': record['min_price'],
            'max_price': record['max_price'],
            'modal_price': record['modal_price'],
            'arrival_date': datetime.utcnow().date().isoformat(),
            'data_source': 'demo_fallback',
            'raw_unit': self.settings.mandi_price_default_price_unit,
        }]

    def _convert_to_price_per_kg(self, value: Any, raw_unit: str) -> float | None:
        if value in (None, ''):
            return None
        try:
            amount = float(value)
        except (TypeError, ValueError):
            return None
        unit = (raw_unit or '').strip().lower()
        if unit == 'quintal':
            return round(amount / 100.0, 2)
        return round(amount, 2)

    def _build_reference(self, record: dict[str, Any], *, product_name: str) -> MarketPriceReference:
        raw_unit = str(record.get('raw_unit') or self.settings.mandi_price_default_price_unit or 'quintal')
        modal_per_kg = self._convert_to_price_per_kg(record.get('modal_price'), raw_unit)
        min_per_kg = self._convert_to_price_per_kg(record.get('min_price'), raw_unit)
        max_per_kg = self._convert_to_price_per_kg(record.get('max_price'), raw_unit)
        return MarketPriceReference(
            product_name=product_name,
            normalized_commodity=self._normalize_commodity(record.get('commodity') or product_name),
            state=record.get('state'),
            district=record.get('district'),
            market=record.get('market'),
            mandi_min_price_per_kg=min_per_kg,
            mandi_max_price_per_kg=max_per_kg,
            mandi_modal_price_per_kg=modal_per_kg,
            mandi_modal_price_raw=float(record.get('modal_price')) if record.get('modal_price') not in (None, '') else None,
            raw_unit=raw_unit,
            arrival_date=record.get('arrival_date'),
            data_source=str(record.get('data_source') or 'gov_api'),
            confidence=0.85 if record.get('data_source') == 'gov_api' else 0.45,
            suggested_price_per_kg=modal_per_kg,
            suggested_min_price_per_kg=min_per_kg,
            suggested_max_price_per_kg=max_per_kg,
            explanation='Recent mandi reference converted to Rs/kg for seller pricing decisions.',
        )

    def _fetch_remote_records(
        self,
        *,
        commodity: str,
        state: str | None,
        district: str | None,
        market: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        if not self.settings.mandi_price_api_key:
            return self._fallback_records(commodity)

        params = {
            'api-key': self.settings.mandi_price_api_key,
            'format': 'json',
            'limit': limit,
            'filters[commodity]': self._normalize_commodity(commodity),
        }
        if state:
            params['filters[state]'] = state
        if district:
            params['filters[district]'] = district
        if market:
            params['filters[market]'] = market

        try:
            response = httpx.get(self.settings.mandi_price_api_url, params=params, timeout=20.0)
            response.raise_for_status()
            payload = response.json()
            records = payload.get('records') or []
        except (httpx.HTTPError, ValueError):
            return self._fallback_records(commodity)

        normalized = []
        for item in records:
            normalized.append({
                'commodity': item.get('commodity') or commodity,
                'state': item.get('state'),
                'district': item.get('district'),
                'market': item.get('market'),
                'min_price': item.get('min_price'),
                'max_price': item.get('max_price'),
                'modal_price': item.get('modal_price'),
                'arrival_date': item.get('arrival_date'),
                'data_source': 'gov_api',
                'raw_unit': self.settings.mandi_price_default_price_unit,
            })
        return normalized or self._fallback_records(commodity)

    def get_market_prices(
        self,
        commodity: str,
        state: str | None = None,
        district: str | None = None,
        market: str | None = None,
        limit: int = 20,
    ) -> list[MarketPriceReference]:
        effective_state = state or self.settings.mandi_price_default_state
        cache_key = self._cache_key(commodity, effective_state, district, market)
        cached = self._cache.get(cache_key)
        now = datetime.utcnow()
        if cached and cached[0] >= now:
            return cached[1]

        records = self._fetch_remote_records(
            commodity=commodity,
            state=effective_state,
            district=district,
            market=market,
            limit=limit,
        )
        references = [self._build_reference(record, product_name=self._normalize_commodity(commodity)) for record in records]
        expires_at = now + timedelta(minutes=self.settings.mandi_price_cache_ttl_minutes)
        self._cache[cache_key] = (expires_at, references)
        return references

    def get_best_market_reference(
        self,
        product_name: str,
        pickup_location: str | None = None,
        state: str | None = None,
        district: str | None = None,
    ) -> MarketPriceReference | None:
        market = None
        if pickup_location:
            market = pickup_location.split(',')[0].strip() or None
        prices = self.get_market_prices(product_name, state=state, district=district, market=market, limit=5)
        return prices[0] if prices else None

    def suggest_listing_price(
        self,
        product_name: str,
        quality_grade: str | None = None,
        seller_price: float | None = None,
        pickup_location: str | None = None,
    ) -> MarketPriceReference | None:
        reference = self.get_best_market_reference(product_name, pickup_location=pickup_location)
        if reference is None or reference.mandi_modal_price_per_kg is None:
            return reference

        margin_multiplier = 1 + (self.settings.dynamic_pricing_margin_percent / 100.0)
        quality_uplift = 0.0
        normalized_grade = (quality_grade or '').strip().lower()
        if normalized_grade in {'premium', 'a'}:
            quality_uplift = self.settings.dynamic_pricing_premium_quality_uplift_percent / 100.0
        elif normalized_grade in {'economy', 'c'}:
            quality_uplift = -(self.settings.dynamic_pricing_economy_discount_percent / 100.0)

        suggested_price = round(reference.mandi_modal_price_per_kg * (margin_multiplier + quality_uplift), 2)
        reference.suggested_price_per_kg = suggested_price
        reference.suggested_min_price_per_kg = round(reference.mandi_modal_price_per_kg * (0.97 + quality_uplift), 2)
        reference.suggested_max_price_per_kg = round(reference.mandi_modal_price_per_kg * (1.08 + quality_uplift), 2)

        if seller_price is None:
            reference.explanation = (
                f'Latest mandi modal is Rs {reference.mandi_modal_price_per_kg}/kg. '
                f'Suggested listing range is Rs {reference.suggested_min_price_per_kg}-Rs {reference.suggested_max_price_per_kg}/kg.'
            )
            return reference

        if seller_price > (reference.suggested_max_price_per_kg or seller_price):
            reference.explanation = (
                f'Your price Rs {seller_price}/kg is above nearby mandi modal Rs {reference.mandi_modal_price_per_kg}/kg. '
                f'Suggested competitive range: Rs {reference.suggested_min_price_per_kg}-Rs {reference.suggested_max_price_per_kg}/kg.'
            )
        elif seller_price < (reference.suggested_min_price_per_kg or seller_price):
            reference.explanation = (
                f'Nearby mandi modal is Rs {reference.mandi_modal_price_per_kg}/kg. '
                f'You may be underpricing. Suggested range: Rs {reference.suggested_min_price_per_kg}-Rs {reference.suggested_max_price_per_kg}/kg.'
            )
        else:
            reference.explanation = (
                f'Your price Rs {seller_price}/kg is within the suggested mandi-informed range '
                f'of Rs {reference.suggested_min_price_per_kg}-Rs {reference.suggested_max_price_per_kg}/kg.'
            )
        return reference
