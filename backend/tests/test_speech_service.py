from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

from app.services.speech_service import SpeechService


class _FakeSpeechClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def recognize(self, *, config, audio):
        self.calls.append({'config': config, 'audio': audio})
        if config.get('sample_rate_hertz') == 16000:
            return SimpleNamespace(
                results=[
                    SimpleNamespace(
                        alternatives=[SimpleNamespace(transcript='tamatar 20 kilo')]
                    )
                ]
            )
        return SimpleNamespace(results=[])


def test_transcribe_bytes_prefers_16000_for_whatsapp_ogg_opus(monkeypatch) -> None:
    fake_client = _FakeSpeechClient()

    speech_module = ModuleType('speech_v1')

    class _AudioEncoding:
        OGG_OPUS = 'OGG_OPUS'
        MP3 = 'MP3'
        ENCODING_UNSPECIFIED = 'ENCODING_UNSPECIFIED'

    class _RecognitionConfig:
        AudioEncoding = _AudioEncoding

        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def get(self, key, default=None):
            return self.kwargs.get(key, default)

    class _RecognitionAudio:
        def __init__(self, *, content):
            self.content = content

    class _SpeechContext:
        def __init__(self, *, phrases):
            self.phrases = phrases

    speech_module.RecognitionConfig = _RecognitionConfig
    speech_module.RecognitionAudio = _RecognitionAudio
    speech_module.SpeechContext = _SpeechContext

    google_module = ModuleType('google')
    cloud_module = ModuleType('google.cloud')
    cloud_module.speech_v1 = speech_module
    google_module.cloud = cloud_module

    monkeypatch.setitem(sys.modules, 'google', google_module)
    monkeypatch.setitem(sys.modules, 'google.cloud', cloud_module)
    monkeypatch.setitem(sys.modules, 'google.cloud.speech_v1', speech_module)

    service = SpeechService()
    monkeypatch.setattr(service.clients, 'speech', lambda: fake_client)

    transcript = service.transcribe_bytes(b'fake-ogg-bytes', 'audio/ogg; codecs=opus')

    assert transcript == 'tamatar 20 kilo'
    assert fake_client.calls
    assert fake_client.calls[0]['config'].get('sample_rate_hertz') == 16000
