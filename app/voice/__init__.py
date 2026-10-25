"""Módulo de procesamiento de voz (VAD, STT, TTS y pipeline en tiempo real)."""

from app.voice.pipeline import VoiceSession
from app.voice.stt import FasterWhisperSTT
from app.voice.tts import LocalTTSService
from app.voice.vad import SileroVoiceDetector

__all__ = [
    "VoiceSession",
    "FasterWhisperSTT",
    "SileroVoiceDetector",
    "LocalTTSService",
]
