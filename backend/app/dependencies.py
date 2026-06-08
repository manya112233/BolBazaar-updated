import logging
from functools import lru_cache

from app.config import get_settings
from app.services.auth_service import AuthService
from app.services.firestore_store import FirestoreStore
from app.services.marketplace import MarketplaceService
from app.services.store import JsonStore

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_store():
    settings = get_settings()
    if settings.storage_mode.lower() == 'firestore':
        try:
            return FirestoreStore()
        except Exception as exc:
            if not settings.allow_local_fallback:
                raise
            logger.warning('Falling back to local JSON store because Firestore is unavailable: %s', exc)
    return JsonStore(file_path=settings.data_file)


@lru_cache(maxsize=1)
def get_marketplace():
    return MarketplaceService(store=get_store())


@lru_cache(maxsize=1)
def get_auth_service():
    return AuthService(store=get_store())
