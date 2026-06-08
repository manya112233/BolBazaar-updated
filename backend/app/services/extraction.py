from __future__ import annotations

import json
import logging
import re
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas import LedgerCaptureMode, LedgerEntry, ListingCreate, ProduceQualityAssessment, ProductCategory, SellerInsight, SourceChannel
from app.services.google_clients import GoogleClients


logger = logging.getLogger(__name__)

PRODUCT_CATALOG: dict[str, dict[str, str]] = {
    'tamatar': {'en': 'Tomato', 'category': 'vegetables'},
    'tomato': {'en': 'Tomato', 'category': 'vegetables'},
    'tomatoes': {'en': 'Tomato', 'category': 'vegetables'},
    'tomatato': {'en': 'Tomato', 'category': 'vegetables'},
    '\u091f\u092e\u093e\u091f\u0930': {'en': 'Tomato', 'category': 'vegetables'},
    'onion': {'en': 'Onion', 'category': 'vegetables'},
    'pyaaz': {'en': 'Onion', 'category': 'vegetables'},
    '\u092a\u094d\u092f\u093e\u091c': {'en': 'Onion', 'category': 'vegetables'},
    '\u092a\u094d\u092f\u093e\u091c\u093c': {'en': 'Onion', 'category': 'vegetables'},
    'spinach': {'en': 'Spinach', 'category': 'vegetables'},
    'palak': {'en': 'Spinach', 'category': 'vegetables'},
    '\u092a\u093e\u0932\u0915': {'en': 'Spinach', 'category': 'vegetables'},
    'potato': {'en': 'Potato', 'category': 'vegetables'},
    'potatoes': {'en': 'Potato', 'category': 'vegetables'},
    'potatao': {'en': 'Potato', 'category': 'vegetables'},
    'potatoe': {'en': 'Potato', 'category': 'vegetables'},
    'potatoo': {'en': 'Potato', 'category': 'vegetables'},
    'potata': {'en': 'Potato', 'category': 'vegetables'},
    'patato': {'en': 'Potato', 'category': 'vegetables'},
    'patata': {'en': 'Potato', 'category': 'vegetables'},
    'batata': {'en': 'Potato', 'category': 'vegetables'},
    'aalu': {'en': 'Potato', 'category': 'vegetables'},
    'alu': {'en': 'Potato', 'category': 'vegetables'},
    'aloo': {'en': 'Potato', 'category': 'vegetables'},
    '\u0906\u0932\u0942': {'en': 'Potato', 'category': 'vegetables'},
    '\u0906\u0932\u0941': {'en': 'Potato', 'category': 'vegetables'},
    '\u092a\u091f\u0947\u091f\u094b': {'en': 'Potato', 'category': 'vegetables'},
    '\u092a\u091f\u0948\u091f\u094b': {'en': 'Potato', 'category': 'vegetables'},
    '\u092a\u091f\u093e\u091f\u094b': {'en': 'Potato', 'category': 'vegetables'},
    '\u092a\u094b\u091f\u0947\u091f\u094b': {'en': 'Potato', 'category': 'vegetables'},
    '\u092a\u094b\u091f\u0948\u091f\u094b': {'en': 'Potato', 'category': 'vegetables'},
    '\u092a\u094b\u091f\u093e\u091f\u094b': {'en': 'Potato', 'category': 'vegetables'},
    '\u092c\u091f\u093e\u091f\u093e': {'en': 'Potato', 'category': 'vegetables'},
    'baingan': {'en': 'Brinjal', 'category': 'vegetables'},
    'brinjal': {'en': 'Brinjal', 'category': 'vegetables'},
    'eggplant': {'en': 'Brinjal', 'category': 'vegetables'},
    '\u092c\u0948\u0902\u0917\u0928': {'en': 'Brinjal', 'category': 'vegetables'},
    'banana': {'en': 'Banana', 'category': 'fruits'},
    'kela': {'en': 'Banana', 'category': 'fruits'},
    '\u0915\u0947\u0932\u093e': {'en': 'Banana', 'category': 'fruits'},
    'bhindi': {'en': 'Okra', 'category': 'vegetables'},
    '\u092d\u093f\u0902\u0921\u0940': {'en': 'Okra', 'category': 'vegetables'},
    'ladyfinger': {'en': 'Okra', 'category': 'vegetables'},
    'okra': {'en': 'Okra', 'category': 'vegetables'},
    'gobi': {'en': 'Cauliflower', 'category': 'vegetables'},
    '\u0917\u094b\u092d\u0940': {'en': 'Cauliflower', 'category': 'vegetables'},
    'cauliflower': {'en': 'Cauliflower', 'category': 'vegetables'},
    'cabbage': {'en': 'Cabbage', 'category': 'vegetables'},
    'patta gobi': {'en': 'Cabbage', 'category': 'vegetables'},
    '\u092a\u0924\u094d\u0924\u093e \u0917\u094b\u092d\u0940': {'en': 'Cabbage', 'category': 'vegetables'},
    'mirchi': {'en': 'Chili', 'category': 'vegetables'},
    '\u092e\u093f\u0930\u094d\u091a\u0940': {'en': 'Chili', 'category': 'vegetables'},
    'chilli': {'en': 'Chili', 'category': 'vegetables'},
    'chili': {'en': 'Chili', 'category': 'vegetables'},
    'lauki': {'en': 'Bottle Gourd', 'category': 'vegetables'},
    '\u0932\u094c\u0915\u0940': {'en': 'Bottle Gourd', 'category': 'vegetables'},
    'bottle gourd': {'en': 'Bottle Gourd', 'category': 'vegetables'},
    'kheera': {'en': 'Cucumber', 'category': 'vegetables'},
    '\u0916\u0940\u0930\u093e': {'en': 'Cucumber', 'category': 'vegetables'},
    'cucumber': {'en': 'Cucumber', 'category': 'vegetables'},
}

ASR_NORMALIZATION_PATTERNS: list[tuple[str, str]] = [
    (r'\bke ji\b', 'kg'),
    (r'\bkej[iy]\b', 'kg'),
    (r'\bkeji\b', 'kg'),
    (r'\bjee kilo\b', 'kilo'),
    (r'\brupiya\b', 'rupaye'),
    (r'\brupee\b', 'rupees'),
    (r'\brupees\b', 'rupees'),
    (r'\brupay\b', 'rupaye'),
    (r'\btamater\b', 'tamatar'),
    (r'\btamator\b', 'tamatar'),
    (r'\bpyaj\b', 'pyaaz'),
    (r'\baaloo\b', 'aloo'),
    (r'\baalu\b', 'aloo'),
    (r'\bpalakh\b', 'palak'),
    (r'\bkataa\b', 'khata'),
    (r'\bkhataa\b', 'khata'),
    (r'\bpick up\b', 'pickup'),
]

DEVANAGARI_DIGIT_MAP = str.maketrans('\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f', '0123456789')
LOCATION_CHARS = r'a-zA-Z\u0900-\u097F'
LOCATION_TOKEN_PATTERN = rf'[{LOCATION_CHARS}]+'
DEFAULT_PRODUCT_NAME = 'Fresh Produce'
DEFAULT_QUANTITY_KG = 25.0
DEFAULT_PRICE_PER_KG = 30.0
DEFAULT_PICKUP_LOCATION = 'Local pickup'
QUANTITY_PATTERN = r'(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilo|kilos|kilogram|kilograms|केजी|\u0915\u093f\u0932\u094b|\u0915\u093f\u0932\u094b\u0917\u094d\u0930\u093e\u092e)'
PRICE_PATTERNS = [
    r'(\d+(?:\.\d+)?)\s*(?:rs\.?|rupees?|rupay|rupaye|rate|bhav|\u0915\u0940\u092e\u0924|\u092d\u093e\u0935|\u0930\u0941\u092a\u092f\u0947|\u0930\u0941\u092a\u090f|\u0930\u0941\u092a\u092f\u093e|\u0930\u0941)\s*(?:/|per)?\s*(?:kg|kilo|केजी|\u0915\u093f\u0932\u094b)?',
    r'(?:rs\.?|rupees?|rupay|rupaye|rate|bhav|\u0915\u0940\u092e\u0924|\u092d\u093e\u0935|\u0930\u0941\u092a\u092f\u0947|\u0930\u0941\u092a\u090f|\u0930\u0941\u092a\u092f\u093e|\u0930\u0941)\s*(\d+(?:\.\d+)?)',
    r'(\d+(?:\.\d+)?)\s*(?:per|har|प्रति)\s*(?:kg|kilo|केजी|\u0915\u093f\u0932\u094b)',
]
MONEY_SIGNAL_PATTERN = (
    r'(?:'
    r'(?:rs\.?|rupees?|rupay|rupaye|rupee|\u0930\u0941\u092a\u092f\u0947|\u0930\u0941\u092a\u090f|\u0930\u0941\u092a\u092f\u093e|\u0930\u0941)\s*(\d+(?:\.\d+)?)'
    r'|'
    r'(\d+(?:\.\d+)?)\s*(?:rs\.?|rupees?|rupay|rupaye|rupee|\u0930\u0941\u092a\u092f\u0947|\u0930\u0941\u092a\u090f|\u0930\u0941\u092a\u092f\u093e|\u0930\u0941)'
    r')'
)
LEDGER_NAME_CHARS = r'a-zA-Z\u0900-\u097F'
LEDGER_SALE_VERB_PATTERN = (
    r'(?:bought|took|purchased|purchase|liya|liye|kharida|kharide|'
    r'\u0916\u0930\u0940\u0926\u093e|\u0932\u093f\u092f\u093e|\u0909\u0920\u093e\u092f\u093e)'
)
LEDGER_PAYMENT_VERB_PATTERN = (
    r'(?:paid|gave|returned|settled|cleared|jama|received|payment|advance|cash|'
    r'diya|\u0926\u093f\u092f\u093e|\u091a\u0941\u0915\u093e\u092f\u093e|\u092d\u0941\u0917\u0924\u093e\u0928(?:\s+\u0915\u093f\u092f\u093e)?)'
)
LEDGER_REQUEST_WORDS = {'ledger', 'khata', 'bahi', 'baki', 'बाकी', 'उधार'}
LEDGER_DUE_PATTERNS = [
    r'(?:owes(?:\s+me)?|owed|due|balance|remaining|still owes|baaki|baki|udhaar|\u092c\u093e\u0915\u0940|\u0909\u0927\u093e\u0930)\s*(?:me\s*)?(?:rs\s*)?(\d+(?:\.\d+)?)',
]
LEDGER_PAID_PATTERNS = [
    r'(?:paid(?:\s+me)?|gave(?:\s+me)?|returned|settled|cleared|received|cash|advance|payment|diya|\u0926\u093f\u092f\u093e|\u091a\u0941\u0915\u093e\u092f\u093e|\u092d\u0941\u0917\u0924\u093e\u0928(?:\s+\u0915\u093f\u092f\u093e)?)\s*(?:rs\s*)?(\d+(?:\.\d+)?)',
]
LEDGER_TOTAL_PATTERNS = [
    r'(?:for|worth|total(?: amount)?|bill(?: amount)?|ka|ki|ke)\s*(?:rs\s*)?(\d+(?:\.\d+)?)',
]
LEDGER_NAME_STOPWORDS = {
    'today',
    'aaj',
    'aj',
    'yesterday',
    'kal',
    'has',
    'have',
    'customer',
    'buyer',
    'mera',
    'meri',
    'mere',
    'hamara',
    'hamare',
    'ne',
}
TRAILING_LOCATION_SUFFIX_PATTERN = r'(?:pickup|pick\s*up|mai|mein|me|\u092e\u0947\u0902)$'
LOCATION_STOPWORDS = {
    'aaj',
    'aj',
    'hai',
    'hain',
    'mera',
    'mere',
    'meri',
    'pass',
    'ka',
    'ki',
    'ke',
    'rs',
    'rupees',
    'rupay',
    'rupaye',
    'kg',
    'kgs',
    'kilo',
    'kilogram',
    'pickup',
    'pick',
    'up',
    'mai',
    'mein',
    'me',
    'at',
    'in',
    'from',
    'stock',
    'fresh',
    '\u0906\u091c',
    '\u0939\u0948',
    '\u0939\u0948\u0902',
    '\u0915\u093e',
    '\u0915\u0940',
    '\u0915\u0947',
    '\u0930\u0941',
    '\u0930\u0941\u092a\u092f\u0947',
    '\u0930\u0941\u092a\u090f',
    '\u0930\u0941\u092a\u092f\u093e',
    '\u0915\u093f\u0932\u094b',
    '\u0915\u093f\u0932\u094b\u0917\u094d\u0930\u093e\u092e',
    '\u092e\u0947\u0902',
}
LOCATION_MIN_WORDS = 1
LOCATION_MAX_WORDS = 4
VALID_PRODUCT_CATEGORIES = {'vegetables', 'fruits', 'grains', 'spices', 'other'}


class ListingExtractionModel(BaseModel):
    product_name: str = Field(description='English product name')
    category: str = Field(description='One of vegetables, fruits, grains, spices, other')
    quantity_kg: float = Field(description='Quantity in kilograms')
    price_per_kg: float = Field(description='Unit price in INR per kilogram')
    pickup_location: str = Field(description='Seller pickup point or locality')
    quality_grade: str = Field(description='standard, premium, economy, etc.')
    description: str = Field(description='Short buyer-facing description')
    tags: list[str] = Field(description='Concise tags for ranking and filtering')


class ProduceQualityAssessmentModel(BaseModel):
    quality_grade: str = Field(description='Use premium, standard, or economy based only on visible freshness cues.')
    quality_score: int = Field(ge=0, le=100, description='Visible freshness score from 0 to 100.')
    quality_summary: str = Field(description='One short buyer-facing summary of visible freshness, blemishes, and ripeness.')
    quality_signals: list[str] = Field(description='Short visible cues such as color consistency, ripeness, or blemishes.')
    detected_product_name: str | None = Field(
        default=None,
        description='Visible produce type in singular English, such as Tomato or Potato. Use null if unclear.',
    )
    detected_category: str | None = Field(
        default=None,
        description='One of vegetables, fruits, grains, spices, other. Use null if unclear.',
    )
    estimated_visible_count: int | None = Field(
        default=None,
        ge=0,
        description='Approximate count of visible individual pieces only. Do not convert this to kilograms.',
    )


class InsightModel(BaseModel):
    headline: str
    message: str


class LedgerExtractionModel(BaseModel):
    entry_kind: str = Field(description='Use sale or payment.')
    buyer_name: str = Field(description='Buyer or customer name.')
    product_name: str | None = Field(default=None, description='English produce name when present.')
    quantity_kg: float | None = Field(default=None, description='Quantity in kilograms when present.')
    total_amount: float | None = Field(default=None, description='Total bill amount in INR.')
    amount_paid: float | None = Field(default=None, description='Amount already paid in INR.')
    amount_due: float | None = Field(default=None, description='Amount still due in INR.')
    summary: str | None = Field(default=None, description='Short seller-facing khata summary.')


class ExtractionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.clients = GoogleClients()
        self._image_assessment_cache: dict[str, ProduceQualityAssessment] = {}

    def _normalize_message(self, message: str) -> str:
        normalized = message.translate(DEVANAGARI_DIGIT_MAP)
        normalized = normalized.replace('\u20b9', ' rs ')
        normalized = re.sub(r'\s+', ' ', normalized.lower()).strip()
        for pattern, replacement in ASR_NORMALIZATION_PATTERNS:
            normalized = re.sub(pattern, replacement, normalized)
        return normalized

    def _format_location(self, location: str) -> str:
        cleaned = location.strip(' ,.-')
        if re.search(r'[a-zA-Z]', cleaned):
            return ' '.join(part.capitalize() for part in cleaned.split())
        return cleaned

    def _build_description(self, product_name: str, seller_name: str, location: str) -> str:
        return f'{product_name} from {seller_name}, available for same-day pickup at {location}.'

    def _normalize_quality_grade(self, quality_grade: str | None) -> str:
        normalized = (quality_grade or '').strip().lower()
        if normalized in {'premium', 'standard', 'economy'}:
            return normalized
        if normalized in {'high', 'high quality', 'top'}:
            return 'premium'
        if normalized in {'low', 'low quality', 'basic'}:
            return 'economy'
        return 'standard'

    def _normalize_category(self, category: str | None) -> ProductCategory | None:
        normalized = (category or '').strip().lower()
        if normalized in VALID_PRODUCT_CATEGORIES:
            return normalized  # type: ignore[return-value]
        return None

    def _normalize_detected_product(self, product_name: str | None) -> tuple[str | None, ProductCategory | None]:
        normalized = self._normalize_message(product_name or '')
        if not normalized or normalized in {'unknown', 'unclear', 'produce', 'vegetable', 'vegetables', 'fruit', 'fruits'}:
            return None, None

        for key, value in PRODUCT_CATALOG.items():
            if key == normalized or re.search(rf'\b{re.escape(key)}\b', normalized):
                return value['en'], self._normalize_category(value['category'])

        cleaned = re.sub(r'[^a-zA-Z\u0900-\u097F\s-]', ' ', product_name or '')
        cleaned = re.sub(r'\s+', ' ', cleaned).strip(' ,-')
        if not cleaned:
            return None, None
        if re.search(r'[a-zA-Z]', cleaned):
            cleaned = ' '.join(part.capitalize() for part in cleaned.split())
        return cleaned, 'other'

    def _image_assessment_cache_key(self, image_bytes: bytes, mime_type: str, product_hint: str | None) -> str:
        digest = sha256()
        digest.update(mime_type.lower().encode('utf-8'))
        digest.update(b'\0')
        digest.update((product_hint or '').strip().lower().encode('utf-8'))
        digest.update(b'\0')
        digest.update(image_bytes)
        return digest.hexdigest()

    def _image_assessment_models(self) -> list[str]:
        candidates = [
            self.settings.gemini_vision_model,
            self.settings.gemini_model,
            *self.settings.gemini_vision_fallback_models.split(','),
        ]
        models: list[str] = []
        for candidate in candidates:
            model = (candidate or '').strip()
            if model and model not in models:
                models.append(model)
        return models

    def _is_quota_error(self, exc: Exception) -> bool:
        message = str(exc)
        return '429' in message or 'RESOURCE_EXHAUSTED' in message or 'quota' in message.lower()

    def _build_tags(
        self,
        category: str,
        quality_grade: str,
        product_name: str,
        source_channel: SourceChannel,
        quality_assessment_source: str = 'text_signal',
    ) -> list[str]:
        tags = [category, self._normalize_quality_grade(quality_grade), product_name.lower(), source_channel]
        if quality_assessment_source == 'ai_visual':
            tags.append('photo_checked')
        # Keep tags stable and deduplicated for ranking/filtering.
        return list(dict.fromkeys(tags))

    def _merge_quality_assessment(
        self,
        listing: ListingCreate,
        quality_assessment: ProduceQualityAssessment | None,
    ) -> ListingCreate:
        if quality_assessment is None:
            return listing

        listing.quality_grade = self._normalize_quality_grade(quality_assessment.quality_grade)
        listing.quality_score = quality_assessment.quality_score
        listing.quality_summary = (quality_assessment.quality_summary or '').strip() or None
        listing.quality_assessment_source = quality_assessment.quality_assessment_source
        listing.quality_signals = list(dict.fromkeys(signal.strip() for signal in quality_assessment.quality_signals if signal.strip()))
        listing.tags = self._build_tags(
            listing.category,
            listing.quality_grade,
            listing.product_name,
            listing.source_channel,
            listing.quality_assessment_source,
        )
        return listing

    def _extract_trailing_location(self, normalized: str) -> str | None:
        suffix_match = re.search(TRAILING_LOCATION_SUFFIX_PATTERN, normalized)
        if suffix_match is None:
            return None

        tokens = re.findall(LOCATION_TOKEN_PATTERN, normalized[:suffix_match.start()])
        if not tokens:
            return None

        location_tokens: list[str] = []
        for token in reversed(tokens):
            if token in LOCATION_STOPWORDS or any(char.isdigit() for char in token):
                if location_tokens:
                    break
                continue
            location_tokens.append(token)
            if len(location_tokens) >= LOCATION_MAX_WORDS:
                break

        if len(location_tokens) < LOCATION_MIN_WORDS:
            return None
        return self._format_location(' '.join(reversed(location_tokens)))

    def _extract_location(self, normalized: str) -> str:
        explicit_location_patterns = [
            rf'(?:at|in|from)\s+([{LOCATION_CHARS}][{LOCATION_CHARS}\s-]{{1,80}})$',
            rf'(?:pickup|pick\s*up)\s+(?:at\s+|to\s+|in\s+|is\s+)?([{LOCATION_CHARS}][{LOCATION_CHARS}\s-]{{1,80}})$',
            rf'([{LOCATION_CHARS}][{LOCATION_CHARS}\s-]{{1,80}})\s+(?:pickup|pick\s*up)$',
            rf'(?:\u092a\u093f\u0915\u0905\u092a|pickup)\s+(?:at\s+|to\s+|in\s+|is\s+)?([{LOCATION_CHARS}][{LOCATION_CHARS}\s-]{{1,80}})$',
            rf'([{LOCATION_CHARS}][{LOCATION_CHARS}\s-]{{1,80}})\s+(?:\u092a\u093f\u0915\u0905\u092a)$',
            rf'(?:change|update|correct)\s+(?:pickup|pick\s*up|location)\s+(?:to\s+|as\s+)?([{LOCATION_CHARS}][{LOCATION_CHARS}\s-]{{1,80}})$',
        ]
        for pattern in explicit_location_patterns:
            matches = re.findall(pattern, normalized)
            if matches:
                return self._format_location(matches[-1])

        trailing_location = self._extract_trailing_location(normalized)
        if trailing_location:
            return trailing_location
        return DEFAULT_PICKUP_LOCATION

    def _extract_price_signal(self, normalized: str, quantity_kg: float | None = None) -> float | None:
        for pattern in PRICE_PATTERNS:
            match = re.search(pattern, normalized)
            if match:
                candidate = float(match.group(1))
                if quantity_kg is None or abs(candidate - quantity_kg) > 1e-9:
                    return candidate
        return None

    def parse_listing_signals(self, message: str) -> dict[str, Any]:
        normalized = self._normalize_message(message)

        product_name = None
        category = None
        for key, value in PRODUCT_CATALOG.items():
            if key in normalized:
                product_name = value['en']
                category = value['category']
                break

        qty_match = re.search(QUANTITY_PATTERN, normalized)
        quantity_kg = float(qty_match.group(1)) if qty_match else None

        return {
            'product_name': product_name,
            'category': category,
            'quantity_kg': quantity_kg,
            'price_per_kg': self._extract_price_signal(normalized, quantity_kg),
            'pickup_location': self._extract_location(normalized),
        }

    def _format_person_name(self, value: str) -> str:
        cleaned = re.sub(r'\s+', ' ', value.strip(' ,.-')).strip()
        if re.search(r'[a-zA-Z]', cleaned):
            return ' '.join(part.capitalize() for part in cleaned.split())
        return cleaned

    def _normalize_entry_kind(self, value: str | None) -> str:
        normalized = (value or '').strip().lower()
        if normalized in {'payment', 'paid', 'received', 'settlement'}:
            return 'payment'
        return 'sale'

    def _extract_money_values(self, normalized: str) -> list[tuple[float, tuple[int, int]]]:
        matches: list[tuple[float, tuple[int, int]]] = []
        for match in re.finditer(MONEY_SIGNAL_PATTERN, normalized):
            groups = [group for group in match.groups() if group is not None]
            if not groups:
                continue
            matches.append((float(groups[0]), match.span()))
        return matches

    def _extract_amount_match(self, normalized: str, patterns: list[str]) -> tuple[float | None, tuple[int, int] | None]:
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match is None:
                continue
            groups = [group for group in match.groups() if group is not None]
            if not groups:
                continue
            return float(groups[0]), match.span()
        return None, None

    def _extract_ledger_buyer_name(self, normalized: str) -> str | None:
        name_pattern = rf'([{LEDGER_NAME_CHARS}][{LEDGER_NAME_CHARS}\s]{{1,40}}?)\s+(?:ne\s+)?'
        candidate_patterns = [
            rf'^{name_pattern}{LEDGER_SALE_VERB_PATTERN}\b',
            rf'^{name_pattern}{LEDGER_PAYMENT_VERB_PATTERN}\b',
            rf'{name_pattern}{LEDGER_SALE_VERB_PATTERN}\b',
            rf'{name_pattern}{LEDGER_PAYMENT_VERB_PATTERN}\b',
        ]

        for pattern in candidate_patterns:
            match = re.search(pattern, normalized)
            if match is None:
                continue
            candidate = match.group(1).strip()
            tokens = [token for token in candidate.split() if token]
            while tokens and tokens[0] in LEDGER_NAME_STOPWORDS:
                tokens.pop(0)
            while tokens and tokens[-1] in LEDGER_NAME_STOPWORDS:
                tokens.pop()
            if not tokens:
                continue
            return self._format_person_name(' '.join(tokens))
        return None

    def _format_amount(self, value: float | None) -> str:
        return f'{value:g}' if value is not None else '0'

    def _build_ledger_summary(
        self,
        *,
        buyer_name: str,
        entry_kind: str,
        product_name: str | None,
        quantity_kg: float | None,
        total_amount: float | None,
        amount_paid: float,
        amount_due: float,
    ) -> str:
        if entry_kind == 'payment':
            return f'{buyer_name} paid Rs {self._format_amount(amount_paid)} toward the khata balance.'

        if product_name and quantity_kg is not None:
            opening = f'{buyer_name} bought {quantity_kg:g} kg {product_name}.'
        elif product_name:
            opening = f'{buyer_name} bought {product_name}.'
        else:
            opening = f'{buyer_name} purchase recorded.'

        details: list[str] = []
        if total_amount is not None:
            details.append(f'Total Rs {self._format_amount(total_amount)}')
        if amount_paid > 0:
            details.append(f'paid Rs {self._format_amount(amount_paid)}')
        if amount_due > 0:
            details.append(f'due Rs {self._format_amount(amount_due)}')

        if not details:
            return opening
        return f'{opening} {", ".join(details)}.'.replace('.,', '.')

    def _finalize_ledger_amounts(
        self,
        *,
        entry_kind: str,
        total_amount: float | None,
        amount_paid: float | None,
        amount_due: float | None,
    ) -> tuple[float | None, float, float, float]:
        total = round(total_amount, 2) if total_amount is not None else None
        paid = round(amount_paid, 2) if amount_paid is not None else None
        due = round(amount_due, 2) if amount_due is not None else None

        if entry_kind == 'payment':
            payment_amount = paid if paid is not None else total if total is not None else due if due is not None else 0.0
            payment_amount = max(round(payment_amount, 2), 0.0)
            return payment_amount, payment_amount, 0.0, -payment_amount

        if total is None and paid is not None and due is not None:
            total = round(paid + due, 2)
        elif total is None and paid is not None:
            total = paid
        elif total is None and due is not None:
            total = due

        if paid is None and due is not None and total is not None:
            paid = max(round(total - due, 2), 0.0)
        elif due is None and paid is not None and total is not None:
            due = max(round(total - paid, 2), 0.0)

        if paid is None and due is None and total is not None:
            paid = total
            due = 0.0

        paid = max(round(paid or 0.0, 2), 0.0)
        due = max(round(due or 0.0, 2), 0.0)
        if total is not None:
            total = round(max(total, paid + due), 2)
        return total, paid, due, due

    def _create_ledger_entry(
        self,
        *,
        seller_id: str,
        buyer_name: str,
        entry_kind: str,
        product_name: str | None,
        quantity_kg: float | None,
        total_amount: float | None,
        amount_paid: float | None,
        amount_due: float | None,
        summary: str | None,
        source_channel: SourceChannel,
        capture_mode: LedgerCaptureMode,
        raw_message: str,
        parse_source: str,
    ) -> LedgerEntry:
        normalized_kind = self._normalize_entry_kind(entry_kind)
        normalized_total, normalized_paid, normalized_due, balance_delta = self._finalize_ledger_amounts(
            entry_kind=normalized_kind,
            total_amount=total_amount,
            amount_paid=amount_paid,
            amount_due=amount_due,
        )
        normalized_buyer = self._format_person_name(buyer_name)
        normalized_product = product_name.strip() if product_name else None
        final_summary = (summary or '').strip() or self._build_ledger_summary(
            buyer_name=normalized_buyer,
            entry_kind=normalized_kind,
            product_name=normalized_product,
            quantity_kg=quantity_kg,
            total_amount=normalized_total,
            amount_paid=normalized_paid,
            amount_due=normalized_due,
        )

        return LedgerEntry(
            seller_id=seller_id,
            buyer_name=normalized_buyer,
            entry_kind=normalized_kind,  # type: ignore[arg-type]
            product_name=normalized_product,
            quantity_kg=quantity_kg,
            total_amount=normalized_total,
            amount_paid=normalized_paid,
            amount_due=normalized_due,
            balance_delta=balance_delta,
            summary=final_summary,
            source_channel=source_channel,
            capture_mode=capture_mode,
            parse_source=parse_source,  # type: ignore[arg-type]
            raw_message=raw_message,
        )

    def _regex_extract_ledger(
        self,
        *,
        message: str,
        seller_id: str,
        source_channel: SourceChannel,
        capture_mode: LedgerCaptureMode,
    ) -> LedgerEntry | None:
        normalized = self._normalize_message(message)
        buyer_name = self._extract_ledger_buyer_name(normalized)
        if not buyer_name:
            return None

        money_values = self._extract_money_values(normalized)
        if not money_values:
            return None

        listing_signals = self.parse_listing_signals(message)
        product_name = listing_signals.get('product_name')
        quantity_kg = listing_signals.get('quantity_kg')
        price_per_kg = listing_signals.get('price_per_kg')

        has_sale_verb = re.search(rf'\b{LEDGER_SALE_VERB_PATTERN}\b', normalized) is not None
        has_payment_verb = re.search(rf'\b{LEDGER_PAYMENT_VERB_PATTERN}\b', normalized) is not None
        if has_payment_verb and not has_sale_verb:
            entry_kind = 'payment'
        elif has_sale_verb or product_name or quantity_kg is not None:
            entry_kind = 'sale'
        else:
            entry_kind = 'payment'

        due_amount, due_span = self._extract_amount_match(normalized, LEDGER_DUE_PATTERNS)
        paid_amount, paid_span = self._extract_amount_match(normalized, LEDGER_PAID_PATTERNS)
        total_amount, total_span = self._extract_amount_match(normalized, LEDGER_TOTAL_PATTERNS)

        if total_amount is None and quantity_kg is not None and price_per_kg is not None:
            total_amount = round(quantity_kg * price_per_kg, 2)

        if total_amount is None:
            blocked_spans = [span for span in [due_span, paid_span] if span is not None]
            for value, span in money_values:
                if any(span == blocked_span for blocked_span in blocked_spans):
                    continue
                total_amount = value
                total_span = span
                break

        if entry_kind == 'payment' and paid_amount is None:
            paid_amount = total_amount if total_amount is not None else money_values[0][0]

        if entry_kind == 'sale' and total_amount is None and paid_amount is not None and due_amount is not None:
            total_amount = round(paid_amount + due_amount, 2)
        elif entry_kind == 'sale' and total_amount is None and total_span is None and len(money_values) == 1:
            total_amount = money_values[0][0]

        return self._create_ledger_entry(
            seller_id=seller_id,
            buyer_name=buyer_name,
            entry_kind=entry_kind,
            product_name=product_name,
            quantity_kg=quantity_kg,
            total_amount=total_amount,
            amount_paid=paid_amount,
            amount_due=due_amount,
            summary=None,
            source_channel=source_channel,
            capture_mode=capture_mode,
            raw_message=message,
            parse_source='rule_based',
        )

    def _apply_location_fallback(self, listing: ListingCreate, default_pickup_location: str | None) -> ListingCreate:
        if default_pickup_location and listing.pickup_location == DEFAULT_PICKUP_LOCATION:
            listing.pickup_location = default_pickup_location

        if not listing.description or DEFAULT_PICKUP_LOCATION.lower() in listing.description.lower():
            listing.description = self._build_description(listing.product_name, listing.seller_name, listing.pickup_location)
        if not listing.tags:
            listing.tags = self._build_tags(
                listing.category,
                listing.quality_grade,
                listing.product_name,
                listing.source_channel,
                listing.quality_assessment_source,
            )
        return listing

    def _regex_extract(
        self,
        message: str,
        seller_id: str,
        seller_name: str,
        image_url: str | None,
        source_channel: SourceChannel,
        default_pickup_location: str | None = None,
    ) -> ListingCreate:
        normalized = self._normalize_message(message)

        product_name = DEFAULT_PRODUCT_NAME
        category = 'vegetables'
        for key, value in PRODUCT_CATALOG.items():
            if key in normalized:
                product_name = value['en']
                category = value['category']
                break

        qty_match = re.search(QUANTITY_PATTERN, normalized)
        quantity_kg = float(qty_match.group(1)) if qty_match else DEFAULT_QUANTITY_KG

        price_per_kg = None
        for pattern in PRICE_PATTERNS:
            match = re.search(pattern, normalized)
            if match:
                candidate = float(match.group(1))
                if candidate != quantity_kg:
                    price_per_kg = candidate
                    break
        if price_per_kg is None:
            numeric_values = [float(value) for value in re.findall(r'\d+(?:\.\d+)?', normalized)]
            filtered_values = [value for value in numeric_values if abs(value - quantity_kg) > 1e-9]
            price_per_kg = filtered_values[0] if filtered_values else DEFAULT_PRICE_PER_KG

        location = self._extract_location(normalized)
        quality_grade = 'premium' if any(
            word in normalized
            for word in [
                'fresh',
                'achha',
                'premium',
                'good',
                '\u0924\u093e\u091c\u093e',
                '\u0924\u093e\u091c\u093c\u093e',
                '\u0905\u091a\u094d\u091b\u093e',
            ]
        ) else 'standard'

        listing = ListingCreate(
            seller_id=seller_id,
            seller_name=seller_name,
            product_name=product_name,
            category=category,  # type: ignore[arg-type]
            quantity_kg=quantity_kg,
            price_per_kg=price_per_kg,
            pickup_location=location,
            quality_grade=self._normalize_quality_grade(quality_grade),
            image_url=image_url,
            description=self._build_description(product_name, seller_name, location),
            tags=self._build_tags(category, quality_grade, product_name, source_channel),
            source_channel=source_channel,
            raw_message=message,
        )
        return self._apply_location_fallback(listing, default_pickup_location)

    def _should_prefer_regex(self, message: str, listing: ListingCreate) -> bool:
        normalized = self._normalize_message(message)
        has_product_signal = any(key in normalized for key in PRODUCT_CATALOG)
        has_quantity_signal = re.search(QUANTITY_PATTERN, normalized) is not None
        has_price_signal = any(re.search(pattern, normalized) is not None for pattern in PRICE_PATTERNS)
        return has_product_signal and has_quantity_signal and has_price_signal and listing.product_name != DEFAULT_PRODUCT_NAME

    def has_listing_signal(self, message: str) -> bool:
        signals = self.parse_listing_signals(message)
        return bool(signals['product_name'] and signals['quantity_kg'] and signals['price_per_kg'])

    def has_ledger_signal(self, message: str) -> bool:
        normalized = self._normalize_message(message)
        if not normalized:
            return False
        if any(word in normalized.split() for word in LEDGER_REQUEST_WORDS):
            return True
        if not self._extract_money_values(normalized):
            return False
        if re.search(rf'\b{LEDGER_SALE_VERB_PATTERN}\b', normalized) and self._extract_ledger_buyer_name(normalized):
            return True
        if re.search(rf'\b{LEDGER_PAYMENT_VERB_PATTERN}\b', normalized) and self._extract_ledger_buyer_name(normalized):
            return True
        return any(re.search(pattern, normalized) is not None for pattern in LEDGER_DUE_PATTERNS)

    def _gemini_extract(
        self,
        message: str,
        seller_id: str,
        seller_name: str,
        image_url: str | None,
        source_channel: SourceChannel,
        default_pickup_location: str | None = None,
    ) -> ListingCreate | None:
        client = self.clients.gemini()
        if client is None:
            return None

        prompt = (
            'Extract a produce marketplace listing from this seller transcript. '
            'Return only structured JSON and normalize any Hindi produce name into English. '
            f'Assume INR pricing and kilograms. Transcript: {message}'
        )

        try:
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_json_schema': ListingExtractionModel.model_json_schema(),
                },
            )
        except Exception:
            return None

        raw_text = getattr(response, 'text', None)
        if not raw_text:
            return None

        try:
            payload: dict[str, Any] = json.loads(raw_text)
        except json.JSONDecodeError:
            return None

        payload['seller_id'] = seller_id
        payload['seller_name'] = seller_name
        payload['image_url'] = image_url
        payload['source_channel'] = source_channel
        payload['raw_message'] = message
        try:
            listing = ListingCreate.model_validate(payload)
        except Exception:
            return None
        return self._apply_location_fallback(listing, default_pickup_location)

    def _gemini_extract_ledger(
        self,
        *,
        message: str,
        seller_id: str,
        source_channel: SourceChannel,
        capture_mode: LedgerCaptureMode,
    ) -> LedgerEntry | None:
        client = self.clients.gemini()
        if client is None:
            return None

        prompt = (
            'Extract a farmer khata ledger update from this WhatsApp message. '
            'This is for a rural produce seller ledger. '
            'Decide whether the message is a sale on credit/cash or a payment toward an earlier balance. '
            'Return only structured JSON. Normalize any produce name into English. '
            f'Message: {message}'
        )

        try:
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_json_schema': LedgerExtractionModel.model_json_schema(),
                },
            )
        except Exception:
            return None

        raw_text = getattr(response, 'text', None)
        if not raw_text:
            return None

        try:
            payload = LedgerExtractionModel.model_validate_json(raw_text)
        except Exception:
            return None

        if not payload.buyer_name.strip():
            return None

        return self._create_ledger_entry(
            seller_id=seller_id,
            buyer_name=payload.buyer_name,
            entry_kind=payload.entry_kind,
            product_name=payload.product_name,
            quantity_kg=payload.quantity_kg,
            total_amount=payload.total_amount,
            amount_paid=payload.amount_paid,
            amount_due=payload.amount_due,
            summary=payload.summary,
            source_channel=source_channel,
            capture_mode=capture_mode,
            raw_message=message,
            parse_source='ai_structured',
        )

    def extract_ledger_entry(
        self,
        *,
        message: str,
        seller_id: str,
        source_channel: SourceChannel = 'whatsapp',
        capture_mode: LedgerCaptureMode = 'text_message',
    ) -> LedgerEntry | None:
        regex_entry = self._regex_extract_ledger(
            message=message,
            seller_id=seller_id,
            source_channel=source_channel,
            capture_mode=capture_mode,
        )
        ai_entry = self._gemini_extract_ledger(
            message=message,
            seller_id=seller_id,
            source_channel=source_channel,
            capture_mode=capture_mode,
        )
        return regex_entry or ai_entry

    def assess_produce_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        product_hint: str | None = None,
    ) -> ProduceQualityAssessment | None:
        if not image_bytes or not mime_type.lower().startswith('image/'):
            return None

        cache_key = self._image_assessment_cache_key(image_bytes, mime_type, product_hint)
        cached_assessment = self._image_assessment_cache.get(cache_key)
        if cached_assessment is not None:
            return cached_assessment

        client = self.clients.gemini()
        if client is None:
            logger.warning('Produce image assessment skipped because Gemini client is not configured.')
            return None

        try:
            from google.genai import types
        except ImportError:
            logger.warning('Produce image assessment skipped because google.genai types are unavailable.')
            return None

        product_context = f'Product hint: {product_hint}.' if product_hint else 'Product hint: unknown produce.'
        prompt = (
            'Assess this produce image for a B2B farm marketplace in India. '
            'Identify the visible produce type when it is clear, normalized to singular English. '
            'Look only at visible cues like color consistency, ripeness, blemishes, bruising, shriveling, and freshness. '
            'Estimate visible piece count only if individual pieces are countable. '
            'Do not infer smell, taste, weight, kilograms, or hidden defects. '
            'If the image is unclear or not produce, return quality_grade as standard with a cautious summary. '
            f'{product_context}'
        )

        raw_text = None
        for model_name in self._image_assessment_models():
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        prompt,
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    ],
                    config={
                        'response_mime_type': 'application/json',
                        'response_json_schema': ProduceQualityAssessmentModel.model_json_schema(),
                    },
                )
                raw_text = getattr(response, 'text', None)
                break
            except Exception as exc:
                if self._is_quota_error(exc):
                    logger.warning('Produce image assessment quota exhausted for %s: %s', model_name, exc)
                    continue
                logger.warning('Produce image assessment failed for %s: %s', model_name, exc)
                return None

        if not raw_text:
            logger.warning('Produce image assessment failed because Gemini returned no text.')
            return None

        try:
            payload = ProduceQualityAssessmentModel.model_validate_json(raw_text)
        except Exception as exc:
            logger.warning('Produce image assessment returned invalid JSON: %s', exc)
            return None

        detected_product_name, detected_category = self._normalize_detected_product(payload.detected_product_name)
        detected_category = detected_category or self._normalize_category(payload.detected_category)

        assessment = ProduceQualityAssessment(
            quality_grade=self._normalize_quality_grade(payload.quality_grade),
            quality_score=payload.quality_score,
            quality_summary=payload.quality_summary.strip(),
            quality_assessment_source='ai_visual',
            quality_signals=list(dict.fromkeys(signal.strip() for signal in payload.quality_signals if signal.strip())),
            detected_product_name=detected_product_name,
            detected_category=detected_category,
            estimated_visible_count=payload.estimated_visible_count,
        )
        self._image_assessment_cache[cache_key] = assessment
        return assessment

    def extract_listing(
        self,
        message: str,
        seller_id: str,
        seller_name: str,
        image_url: str | None,
        source_channel: SourceChannel = 'api',
        default_pickup_location: str | None = None,
        quality_assessment: ProduceQualityAssessment | None = None,
    ) -> ListingCreate:
        regex_listing = self._regex_extract(
            message=message,
            seller_id=seller_id,
            seller_name=seller_name,
            image_url=image_url,
            source_channel=source_channel,
            default_pickup_location=default_pickup_location,
        )
        if self._should_prefer_regex(message, regex_listing):
            return self._merge_quality_assessment(regex_listing, quality_assessment)

        extracted = self._gemini_extract(
            message=message,
            seller_id=seller_id,
            seller_name=seller_name,
            image_url=image_url,
            source_channel=source_channel,
            default_pickup_location=default_pickup_location,
        )
        if extracted is not None:
            return self._merge_quality_assessment(extracted, quality_assessment)
        return self._merge_quality_assessment(regex_listing, quality_assessment)

    def build_insight(
        self,
        seller_id: str,
        seller_name: str,
        product_name: str,
        available_kg: float,
        recent_orders: int,
    ) -> SellerInsight:
        client = self.clients.gemini()
        if client is not None:
            prompt = (
                'Write one short, useful business insight for a produce seller in India. '
                'Keep it direct and actionable. '
                f'Seller: {seller_name}. Product: {product_name}. Available kg: {available_kg}. '
                f'Recent accepted orders: {recent_orders}.'
            )
            try:
                response = client.models.generate_content(
                    model=self.settings.gemini_model,
                    contents=prompt,
                    config={
                        'response_mime_type': 'application/json',
                        'response_json_schema': InsightModel.model_json_schema(),
                    },
                )
                raw_text = getattr(response, 'text', None)
                if raw_text:
                    data = InsightModel.model_validate_json(raw_text)
                    return SellerInsight(seller_id=seller_id, headline=data.headline, message=data.message)
            except Exception:
                pass

        if recent_orders > 0:
            headline = 'Demand is active'
            message = f'Your {product_name.lower()} is moving. Keep the remaining stock live and mention same-day pickup for faster closure.'
        elif available_kg > 40:
            headline = 'Large inventory detected'
            message = f'You still have high stock. A small urgency note or slightly sharper price may help sell {product_name.lower()} faster.'
        else:
            headline = 'Fresh listing advantage'
            message = f'Fresh listings convert better. Emphasize quality and pickup timing for your {product_name.lower()} stock.'

        return SellerInsight(seller_id=seller_id, headline=headline, message=message)
