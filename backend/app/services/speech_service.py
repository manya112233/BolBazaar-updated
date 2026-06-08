from __future__ import annotations

import base64
import logging
from typing import Literal

from app.config import get_settings
from app.services.google_clients import GoogleClients

logger = logging.getLogger(__name__)
OGG_OPUS_SAMPLE_RATES = (16000, 48000, None)

VOICE_NOTE_HINTS = [
    'tamatar',
    'tomato',
    'pyaaz',
    'onion',
    'palak',
    'spinach',
    'aloo',
    'potato',
    'kela',
    'banana',
    'kilo',
    'kg',
    'pickup',
    'rupay',
    'rupaye',
    'rupees',
    'rate',
    'price',
    'laxmi nagar',
    'khata',
    'ledger',
    'bahi',
    'menu',
    'dashboard',
    'listing',
    'listings',
    'stock',
    'orders',
    'customers',
    'buyers',
    'grahak',
    'profile',
    'language',
    'bhasha',
    'verify',
    'verification',
    'help',
    'madad',
    'मदद',
    'डैशबोर्ड',
    'लिस्टिंग',
    'खाता',
    'ऑर्डर',
    'भाषा',
    'प्रोफाइल',
    'सत्यापन',
    'किलो',
    'रुपये',
    'रुपया',
    'टमाटर',
    'आलू',
    'प्याज',
    'पालक',
    'केला',
    'पिकअप',
    'जगह',
    'स्थान',
    'open menu',
    'show khata',
]


class SpeechService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.clients = GoogleClients()

    def transcribe_bytes(self, audio_bytes: bytes, mime_type: str = 'audio/ogg') -> str | None:
        if not audio_bytes:
            logger.info('Speech transcription skipped because the audio payload was empty.')
            return None

        client = self.clients.speech()
        if client is None:
            logger.warning('Speech transcription skipped because the Google Speech client could not be initialized.')
            return self._transcribe_with_gemini(audio_bytes=audio_bytes, mime_type=mime_type)
        try:
            from google.cloud import speech_v1 as speech
        except ImportError:
            logger.warning('Speech transcription skipped because google-cloud-speech is not installed.')
            return self._transcribe_with_gemini(audio_bytes=audio_bytes, mime_type=mime_type)

        mime = mime_type.lower()
        sample_rate_candidates: tuple[int | None, ...] = (None,)
        if 'ogg' in mime or 'opus' in mime:
            encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS
            # WhatsApp voice notes usually decode best at 16 kHz, but we keep a
            # fallback pass for providers that normalize Opus at 48 kHz.
            sample_rate_candidates = OGG_OPUS_SAMPLE_RATES
        elif 'mp3' in mime or 'mpeg' in mime:
            encoding = speech.RecognitionConfig.AudioEncoding.MP3
        else:
            encoding = speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED

        config_variants = [
            {
                'language_code': self.settings.default_language,
                'alternative_language_codes': ['en-IN', 'en-US'],
                'model': 'command_and_search',
            },
            {
                'language_code': self.settings.default_language,
                'model': 'default',
            },
            {
                'language_code': 'en-IN',
                'alternative_language_codes': [self.settings.default_language, 'en-US'],
                'model': 'command_and_search',
            },
        ]

        try:
            audio = speech.RecognitionAudio(content=audio_bytes)
            for variant in config_variants:
                for sample_rate_hertz in sample_rate_candidates:
                    config_kwargs = {
                        'encoding': encoding,
                        'language_code': variant['language_code'],
                        'model': variant['model'],
                        'enable_automatic_punctuation': True,
                        'max_alternatives': 3,
                        'speech_contexts': [speech.SpeechContext(phrases=VOICE_NOTE_HINTS)],
                    }
                    if sample_rate_hertz is not None:
                        config_kwargs['sample_rate_hertz'] = sample_rate_hertz
                    alt_languages = variant.get('alternative_language_codes')
                    if alt_languages:
                        config_kwargs['alternative_language_codes'] = alt_languages

                    config = speech.RecognitionConfig(**config_kwargs)
                    try:
                        response = client.recognize(config=config, audio=audio)
                    except Exception as exc:
                        logger.warning(
                            'Speech transcription failed for model=%s language=%s sample_rate=%s: %s',
                            variant['model'],
                            variant['language_code'],
                            sample_rate_hertz or 'auto',
                            exc,
                        )
                        continue

                    text_parts = [result.alternatives[0].transcript for result in response.results if result.alternatives]
                    transcript = ' '.join(text_parts).strip() or None
                    if transcript:
                        logger.info(
                            'Speech transcription succeeded with model=%s language=%s sample_rate=%s',
                            variant['model'],
                            variant['language_code'],
                            sample_rate_hertz or 'auto',
                        )
                        return transcript
        except Exception as exc:
            logger.warning('Speech transcription failed before recognition completed: %s', exc)
            return self._transcribe_with_gemini(audio_bytes=audio_bytes, mime_type=mime_type)

        logger.warning('Speech transcription returned empty transcript.')
        return self._transcribe_with_gemini(audio_bytes=audio_bytes, mime_type=mime_type)

    def _transcribe_with_gemini(self, *, audio_bytes: bytes, mime_type: str) -> str | None:
        client = self.clients.gemini()
        if client is None:
            logger.warning('Gemini audio transcription skipped because the Gemini client is not configured.')
            return None

        try:
            from google.genai import types
        except ImportError:
            logger.warning('Gemini audio transcription skipped because google.genai types are unavailable.')
            return None

        normalized_mime = (mime_type or 'audio/ogg').lower()
        if 'ogg' in normalized_mime or 'opus' in normalized_mime:
            normalized_mime = 'audio/ogg'
        elif 'mpeg' in normalized_mime:
            normalized_mime = 'audio/mpeg'

        prompt = (
            'Transcribe this short WhatsApp voice note from an Indian produce seller. '
            'Return only the spoken transcript text, with no explanation. '
            'Preserve Hindi-English mixed speech, produce names, city/locality names, and quantity-price details. '
            'Do not translate into pure English. Keep common Indian marketplace words like kilo, rupaye, pickup, khata, '
            'tamatar, aloo, pyaaz, and Devanagari words exactly as spoken when possible.'
        )

        try:
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=audio_bytes, mime_type=normalized_mime),
                ],
            )
        except Exception as exc:
            logger.warning('Gemini audio transcription failed: %s', exc)
            return None

        transcript = getattr(response, 'text', None)
        transcript = transcript.strip() if transcript else None
        if transcript:
            logger.info('Gemini audio transcription succeeded.')
        else:
            logger.warning('Gemini audio transcription returned empty transcript.')
        return transcript or None

    def synthesize(self, text: str, gender: Literal['female', 'male'] = 'female') -> str | None:
        client = self.clients.tts()
        if client is None:
            return None
        try:
            from google.cloud import texttospeech_v1 as texttospeech
        except ImportError:
            return None

        try:
            voice_gender = texttospeech.SsmlVoiceGender.FEMALE if gender == 'female' else texttospeech.SsmlVoiceGender.MALE
            voice = texttospeech.VoiceSelectionParams(language_code=self.settings.default_language, ssml_gender=voice_gender)
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        except Exception as exc:
            logger.warning('Text-to-speech synthesis failed: %s', exc)
            return None

        return base64.b64encode(response.audio_content).decode('utf-8')
