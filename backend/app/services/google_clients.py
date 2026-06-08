from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class GoogleClients:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _credential_path(self) -> Path | None:
        raw_path = self.settings.google_application_credentials
        if not raw_path:
            return None

        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path

    def _service_account_credentials(self) -> Any | None:
        credential_path = self._credential_path()
        if credential_path is None:
            return None
        if not credential_path.exists():
            logger.warning('Google credentials file was not found at %s', credential_path)
            return None

        try:
            from google.oauth2 import service_account
        except ImportError:
            logger.warning('google.oauth2.service_account is unavailable; cannot load Google credentials.')
            return None

        try:
            return service_account.Credentials.from_service_account_file(str(credential_path))
        except Exception as exc:
            logger.warning('Failed to load Google credentials from %s: %s', credential_path, exc)
            return None

    def gemini(self) -> Any | None:
        if not self.settings.gemini_api_key:
            return None
        try:
            from google.genai import Client, types
        except ImportError:
            return None
        return Client(
            api_key=self.settings.gemini_api_key,
            http_options=types.HttpOptions(
                clientArgs={'trust_env': False},
                asyncClientArgs={'trust_env': False},
            ),
        )

    def speech(self) -> Any | None:
        try:
            from google.cloud import speech_v1 as speech
        except ImportError:
            logger.warning('google-cloud-speech is unavailable; speech transcription is disabled.')
            return None

        try:
            credentials = self._service_account_credentials()
            if credentials is not None:
                return speech.SpeechClient(credentials=credentials)
            return speech.SpeechClient()
        except Exception as exc:
            logger.warning('Failed to initialize Google Speech client: %s', exc)
            return None

    def tts(self) -> Any | None:
        try:
            from google.cloud import texttospeech_v1 as texttospeech
        except ImportError:
            logger.warning('google-cloud-texttospeech is unavailable; speech synthesis is disabled.')
            return None

        try:
            credentials = self._service_account_credentials()
            if credentials is not None:
                return texttospeech.TextToSpeechClient(credentials=credentials)
            return texttospeech.TextToSpeechClient()
        except Exception as exc:
            logger.warning('Failed to initialize Google Text-to-Speech client: %s', exc)
            return None

    def firestore(self) -> Any | None:
        try:
            from google.cloud import firestore
        except ImportError:
            logger.warning('google-cloud-firestore is unavailable; Firestore storage is disabled.')
            return None

        client_kwargs: dict[str, Any] = {}
        credentials = self._service_account_credentials()
        if credentials is not None:
            client_kwargs['credentials'] = credentials

        project_id = self.settings.gcp_project_id or self.settings.firebase_project_id
        if project_id:
            client_kwargs['project'] = project_id

        try:
            return firestore.Client(**client_kwargs)
        except Exception as exc:
            logger.warning('Failed to initialize Firestore client: %s', exc)
            return None


def safe_b64(data: bytes | None) -> str | None:
    if not data:
        return None
    return base64.b64encode(data).decode('utf-8')


def read_bytes_from_file(path: str | None) -> bytes | None:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        return None
    return file_path.read_bytes()
