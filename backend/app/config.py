from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default='BolBazaar Google Stack API', alias='APP_NAME')
    app_env: str = Field(default='development', alias='APP_ENV')
    api_v1_prefix: str = Field(default='/api', alias='API_V1_PREFIX')
    frontend_origin: str = Field(default='http://localhost:5173', alias='FRONTEND_ORIGIN')

    storage_mode: str = Field(default='firestore', alias='STORAGE_MODE')
    allow_local_fallback: bool = Field(default=True, alias='ALLOW_LOCAL_FALLBACK')
    data_file: Path = Field(default=Path('./data/demo_db.json'), alias='DATA_FILE')
    media_dir: Path = Field(default=Path('./data/media'), alias='MEDIA_DIR')
    api_public_base_url: str = Field(default='http://localhost:8000', alias='API_PUBLIC_BASE_URL')

    gemini_api_key: str | None = Field(default=None, alias='GEMINI_API_KEY')
    gemini_model: str = Field(default='gemini-2.5-flash', alias='GEMINI_MODEL')
    gemini_vision_model: str | None = Field(default=None, alias='GEMINI_VISION_MODEL')
    gemini_vision_fallback_models: str = Field(default='gemini-2.0-flash-lite,gemini-2.0-flash', alias='GEMINI_VISION_FALLBACK_MODELS')

    google_application_credentials: str | None = Field(default=None, alias='GOOGLE_APPLICATION_CREDENTIALS')
    gcp_project_id: str | None = Field(default=None, alias='GCP_PROJECT_ID')
    firebase_project_id: str | None = Field(default=None, alias='FIREBASE_PROJECT_ID')
    maps_api_key: str | None = Field(default=None, alias='MAPS_API_KEY')

    whatsapp_access_token: str | None = Field(default=None, alias='WHATSAPP_ACCESS_TOKEN')
    whatsapp_phone_number_id: str | None = Field(default=None, alias='WHATSAPP_PHONE_NUMBER_ID')
    whatsapp_verify_token: str | None = Field(default=None, alias='WHATSAPP_VERIFY_TOKEN')
    whatsapp_graph_base_url: str = Field(default='https://graph.facebook.com', alias='WHATSAPP_GRAPH_BASE_URL')
    whatsapp_graph_version: str = Field(default='v24.0', alias='WHATSAPP_GRAPH_VERSION')

    default_currency: str = Field(default='INR', alias='DEFAULT_CURRENCY')
    default_language: str = Field(default='hi-IN', alias='DEFAULT_LANGUAGE')

    demand_push_threshold: int = Field(default=3, ge=1, alias='DEMAND_PUSH_THRESHOLD')
    demand_push_window_minutes: int = Field(default=30, ge=1, alias='DEMAND_PUSH_WINDOW_MINUTES')
    demand_push_cooldown_minutes: int = Field(default=30, ge=1, alias='DEMAND_PUSH_COOLDOWN_MINUTES')

    pool_window_hours: int = Field(default=12, ge=1, alias='POOL_WINDOW_HOURS')
    pool_min_buyers: int = Field(default=2, ge=1, alias='POOL_MIN_BUYERS')
    pool_geo_bucket_decimals: int = Field(default=2, alias='POOL_GEO_BUCKET_DECIMALS')
    delivery_base_fee: float = Field(default=35.0, alias='DELIVERY_BASE_FEE')
    delivery_min_fee: float = Field(default=45.0, alias='DELIVERY_MIN_FEE')
    delivery_per_km_fee: float = Field(default=12.0, alias='DELIVERY_PER_KM_FEE')
    delivery_free_radius_km: float = Field(default=0.0, alias='DELIVERY_FREE_RADIUS_KM')
    delivery_weight_included_kg: float = Field(default=10.0, alias='DELIVERY_WEIGHT_INCLUDED_KG')
    delivery_per_extra_kg_fee: float = Field(default=0.75, alias='DELIVERY_PER_EXTRA_KG_FEE')
    delivery_max_fee: float = Field(default=500.0, alias='DELIVERY_MAX_FEE')
    delivery_surge_multiplier: float = Field(default=1.0, alias='DELIVERY_SURGE_MULTIPLIER')

    mandi_price_api_url: str = Field(
        default='https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070',
        alias='MANDI_PRICE_API_URL',
    )
    mandi_price_api_key: str | None = Field(default=None, alias='MANDI_PRICE_API_KEY')
    mandi_price_cache_ttl_minutes: int = Field(default=360, ge=1, alias='MANDI_PRICE_CACHE_TTL_MINUTES')
    mandi_price_default_state: str = Field(default='Maharashtra', alias='MANDI_PRICE_DEFAULT_STATE')
    mandi_price_default_market: str = Field(default='Pune', alias='MANDI_PRICE_DEFAULT_MARKET')
    mandi_price_default_price_unit: str = Field(default='quintal', alias='MANDI_PRICE_DEFAULT_PRICE_UNIT')
    dynamic_pricing_margin_percent: float = Field(default=8.0, alias='DYNAMIC_PRICING_MARGIN_PERCENT')
    dynamic_pricing_premium_quality_uplift_percent: float = Field(default=7.0, alias='DYNAMIC_PRICING_PREMIUM_QUALITY_UPLIFT_PERCENT')
    dynamic_pricing_economy_discount_percent: float = Field(default=5.0, alias='DYNAMIC_PRICING_ECONOMY_DISCOUNT_PERCENT')

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_file.parent.mkdir(parents=True, exist_ok=True)
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    return settings
