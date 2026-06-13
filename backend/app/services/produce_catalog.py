from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProduceImageMatch:
    image_url: str
    image_source: str


LOCAL_GENERIC_PRODUCE = '/media/default-produce/generic-produce.jpg'
LOCAL_GENERIC_VEGETABLES = '/media/default-produce/generic-vegetables.jpg'
LOCAL_GENERIC_FRUITS = '/media/default-produce/generic-fruits.jpg'
LOCAL_POTATO = '/media/default-produce/potato.jpg'
LOCAL_TOMATO = '/media/default-produce/tomato.jpg'

PRODUCE_IMAGE_CATALOG: dict[str, str] = {
    'tomato': LOCAL_TOMATO,
    'onion': 'https://upload.wikimedia.org/wikipedia/commons/2/25/Onion_on_White.JPG',
    'potato': LOCAL_POTATO,
    'carrot': 'https://upload.wikimedia.org/wikipedia/commons/0/05/CarrotDiversityLg.jpg',
    'cabbage': 'https://upload.wikimedia.org/wikipedia/commons/6/6f/Cabbage_and_cross_section_on_white.jpg',
    'cauliflower': 'https://upload.wikimedia.org/wikipedia/commons/a/aa/Cauliflower.JPG',
    'spinach': 'https://upload.wikimedia.org/wikipedia/commons/0/01/Cropped_image_of_spinach_leaves.jpg',
    'leafy greens': 'https://upload.wikimedia.org/wikipedia/commons/0/01/Cropped_image_of_spinach_leaves.jpg',
    'banana': 'https://upload.wikimedia.org/wikipedia/commons/8/8a/Banana-Single.jpg',
    'mango': 'https://upload.wikimedia.org/wikipedia/commons/9/90/Hapus_Mango.jpg',
    'apple': 'https://upload.wikimedia.org/wikipedia/commons/1/15/Red_Apple.jpg',
    'rice': 'https://upload.wikimedia.org/wikipedia/commons/4/40/Rice_plants_%28IRRI%29.jpg',
    'wheat': 'https://upload.wikimedia.org/wikipedia/commons/a/a6/Wheat_close-up.JPG',
    'grains': 'https://upload.wikimedia.org/wikipedia/commons/a/a6/Wheat_close-up.JPG',
    'spices': 'https://upload.wikimedia.org/wikipedia/commons/6/64/Indian_spices.jpg',
    'generic vegetables': LOCAL_GENERIC_VEGETABLES,
    'generic fruits': LOCAL_GENERIC_FRUITS,
    'generic produce': LOCAL_GENERIC_PRODUCE,
}


PRODUCT_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (('tomato', 'tamatar'), 'tomato'),
    (('onion', 'pyaz'), 'onion'),
    (('potato', 'aloo'), 'potato'),
    (('carrot', 'gajar'), 'carrot'),
    (('cabbage', 'patta gobhi'), 'cabbage'),
    (('cauliflower', 'phool gobhi'), 'cauliflower'),
    (('spinach', 'palak'), 'spinach'),
    (('leafy', 'greens', 'saag', 'methi', 'lettuce'), 'leafy greens'),
    (('banana', 'kela'), 'banana'),
    (('mango', 'aam'), 'mango'),
    (('apple', 'seb'), 'apple'),
    (('rice', 'chawal'), 'rice'),
    (('wheat', 'gehun'), 'wheat'),
    (('grain', 'grains', 'cereal'), 'grains'),
    (('spice', 'spices', 'masala', 'haldi', 'mirch', 'jeera'), 'spices'),
]


def resolve_catalog_image(product_name: str | None, category: str | None) -> ProduceImageMatch:
    normalized_product = (product_name or '').strip().lower()
    normalized_category = (category or '').strip().lower()

    for keywords, catalog_key in PRODUCT_KEYWORDS:
        if any(keyword in normalized_product for keyword in keywords):
            return ProduceImageMatch(PRODUCE_IMAGE_CATALOG[catalog_key], 'produce_catalog')

    if any(token in normalized_product for token in ('vegetable', 'veggies', 'sabzi')):
        return ProduceImageMatch(PRODUCE_IMAGE_CATALOG['generic vegetables'], 'produce_catalog')
    if any(token in normalized_product for token in ('fruit', 'fruits')):
        return ProduceImageMatch(PRODUCE_IMAGE_CATALOG['generic fruits'], 'produce_catalog')
    if normalized_category in {'grains', 'spices'} or normalized_product in {'grains', 'spices'}:
        return ProduceImageMatch(PRODUCE_IMAGE_CATALOG[normalized_category], 'produce_catalog')

    return ProduceImageMatch(PRODUCE_IMAGE_CATALOG['generic produce'], 'generic_catalog')
