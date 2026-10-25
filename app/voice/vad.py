from typing import Optional
import numpy as np
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams


class SileroVoiceDetector:
    """Detector de actividad por voz (VAD) utilizando Silero VAD para detectar habla e interrupciones."""

    def __init__(self, sample_rate: int = 16000, confidence_threshold: float = 0.5):
        self.sample_rate = sample_rate
        self.confidence_threshold = confidence_threshold
        self._vad = SileroVADAnalyzer(
            params=VADParams(
                confidence=confidence_threshold,
                start_secs=0.2,
                stop_secs=0.5,
            )
        )
        self._vad.set_sample_rate(sample_rate)

    def voice_confidence(self, pcm_chunk: bytes) -> float:
        """Calcula la probabilidad de que el chunk de audio contenga voz humana."""
        if not pcm_chunk or len(pcm_chunk) < 1024:
            return 0.0
        # Silero espera frames de 512 muestras int16 (1024 bytes) a 16kHz
        chunk_window = pcm_chunk[:1024]
        conf = self._vad.voice_confidence(chunk_window)
        try:
            return float(conf[0] if isinstance(conf, (list, np.ndarray)) else conf)
        except (IndexError, TypeError, ValueError):
            return 0.0

    def is_speech(self, pcm_chunk: bytes) -> bool:
        """Determina si un fragmento de audio supera el umbral de voz humana."""
        return self.voice_confidence(pcm_chunk) >= self.confidence_threshold

