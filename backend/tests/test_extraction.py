from app.schemas import ListingCreate, ProduceQualityAssessment
from app.services.extraction import ExtractionService


def test_regex_extraction_hindi_price_and_quantity() -> None:
    service = ExtractionService()
    listing = service.extract_listing(
        message='Aaj 50 kilo tamatar hai, 28 rupay kilo, Laxmi Nagar pickup',
        seller_id='seller-1',
        seller_name='Shakti FPO',
        image_url=None,
        source_channel='demo',
    )

    assert listing.product_name == 'Tomato'
    assert listing.quantity_kg == 50.0
    assert listing.price_per_kg == 28.0
    assert 'Laxmi Nagar' in listing.pickup_location


def test_regex_extraction_romanized_location_suffix() -> None:
    service = ExtractionService()
    listing = service.extract_listing(
        message='Mere pass 30 kilo pyaaz hai 28 rupay kilo shanti nagar mai',
        seller_id='seller-2',
        seller_name='Krishi Seller',
        image_url=None,
        source_channel='whatsapp',
    )

    assert listing.product_name == 'Onion'
    assert listing.quantity_kg == 30.0
    assert listing.price_per_kg == 28.0
    assert listing.pickup_location == 'Shanti Nagar'


def test_extract_listing_uses_registered_location_fallback() -> None:
    service = ExtractionService()
    listing = service.extract_listing(
        message='Aaj 20 kilo aloo hai 30 rupay kilo',
        seller_id='seller-2',
        seller_name='Krishi Seller',
        image_url=None,
        source_channel='whatsapp',
        default_pickup_location='Shanti Nagar, Delhi',
    )

    assert listing.product_name == 'Potato'
    assert listing.quantity_kg == 20.0
    assert listing.price_per_kg == 30.0
    assert listing.pickup_location == 'Shanti Nagar, Delhi'


def test_voice_transcription_variant_potatao_maps_to_potato() -> None:
    service = ExtractionService()

    signals = service.parse_listing_signals('potatao 20 kilo 30 rupees kilo')

    assert signals['product_name'] == 'Potato'
    assert signals['quantity_kg'] == 20.0
    assert signals['price_per_kg'] == 30.0


def test_hindi_script_voice_variant_maps_to_potato() -> None:
    service = ExtractionService()

    signals = service.parse_listing_signals('20 किलो पटेटो ₹30 किलो। पोटैटो!')

    assert signals['product_name'] == 'Potato'
    assert signals['quantity_kg'] == 20.0
    assert signals['price_per_kg'] == 30.0


def test_listing_signal_parses_pickup_correction() -> None:
    service = ExtractionService()

    signals = service.parse_listing_signals('change pickup to Nehru Place')

    assert signals['pickup_location'] == 'Nehru Place'


def test_extract_listing_prefers_regex_over_bad_gemini_for_clear_message() -> None:
    service = ExtractionService()

    def fake_gemini_extract(**_: object) -> ListingCreate:
        return ListingCreate(
            seller_id='seller-2',
            seller_name='Krishi Seller',
            product_name='Tomato',
            category='vegetables',
            quantity_kg=25.0,
            price_per_kg=20.0,
            pickup_location='Local pickup',
            quality_grade='standard',
            image_url=None,
            description='Wrong Gemini extraction.',
            tags=['vegetables', 'standard', 'tomato', 'whatsapp'],
            source_channel='whatsapp',
            raw_message='wrong',
        )

    service._gemini_extract = fake_gemini_extract  # type: ignore[method-assign]

    listing = service.extract_listing(
        message='Aaj 20 kilo aloo hai 30 rupay kilo shanti nagar mai',
        seller_id='seller-2',
        seller_name='Krishi Seller',
        image_url=None,
        source_channel='whatsapp',
    )

    assert listing.product_name == 'Potato'
    assert listing.quantity_kg == 20.0
    assert listing.price_per_kg == 30.0
    assert listing.pickup_location == 'Shanti Nagar'


def test_extract_listing_merges_visual_quality_assessment() -> None:
    service = ExtractionService()
    assessment = ProduceQualityAssessment(
        quality_grade='premium',
        quality_score=91,
        quality_summary='Bright red color with minimal visible blemishes.',
        quality_assessment_source='ai_visual',
        quality_signals=['bright red color', 'minimal blemishes'],
    )

    listing = service.extract_listing(
        message='Aaj 20 kilo tamatar hai, 30 rupay kilo, Laxmi Nagar pickup',
        seller_id='seller-3',
        seller_name='Fresh Farm',
        image_url=None,
        source_channel='whatsapp',
        quality_assessment=assessment,
    )

    assert listing.quality_grade == 'premium'
    assert listing.quality_score == 91
    assert listing.quality_summary == 'Bright red color with minimal visible blemishes.'
    assert listing.quality_assessment_source == 'ai_visual'
    assert listing.quality_signals == ['bright red color', 'minimal blemishes']
    assert 'photo_checked' in listing.tags


def test_extract_ledger_entry_parses_sale_with_due_amount() -> None:
    service = ExtractionService()

    entry = service.extract_ledger_entry(
        message='Raju bought 10 kg tomatoes for Rs 250 today, but still owes me Rs 50.',
        seller_id='seller-1',
        source_channel='whatsapp',
        capture_mode='voice_note',
    )

    assert entry is not None
    assert entry.buyer_name == 'Raju'
    assert entry.entry_kind == 'sale'
    assert entry.product_name == 'Tomato'
    assert entry.quantity_kg == 10.0
    assert entry.total_amount == 250.0
    assert entry.amount_paid == 200.0
    assert entry.amount_due == 50.0
    assert entry.balance_delta == 50.0
    assert entry.capture_mode == 'voice_note'


def test_extract_ledger_entry_parses_payment_note() -> None:
    service = ExtractionService()

    entry = service.extract_ledger_entry(
        message='Raju paid Rs 50 today for the earlier tomato balance.',
        seller_id='seller-1',
        source_channel='whatsapp',
        capture_mode='text_message',
    )

    assert entry is not None
    assert entry.buyer_name == 'Raju'
    assert entry.entry_kind == 'payment'
    assert entry.amount_paid == 50.0
    assert entry.amount_due == 0.0
    assert entry.balance_delta == -50.0
    assert entry.capture_mode == 'text_message'
