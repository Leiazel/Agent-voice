import io
import wave
from pathlib import Path
from typing import Optional
import numpy as np
from faster_whisper import WhisperModel
from app.config import settings


class FasterWhisperSTT:
    """Servicio de Speech-to-Text utilizando faster-whisper en CPU con precisión int8."""

    _instance: Optional["FasterWhisperSTT"] = None
    _model: Optional[WhisperModel] = None

    def __init__(self, model_name: str | None = None, device: str = "cpu", compute_type: str = "int8"):
        self.model_name = model_name or settings.stt_model
        self.device = device
        self.compute_type = compute_type

    def get_model(self) -> WhisperModel:
        if FasterWhisperSTT._model is None:
            # Si el modelo configurado es "base" pero la máquina es modesta, tiny o base corren muy rápido
            FasterWhisperSTT._model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
        return FasterWhisperSTT._model

    def transcribe_audio_bytes(self, pcm_bytes: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe un buffer de audio PCM de 16 bits monoaural a texto en español.
        """
        if not pcm_bytes:
            return ""

        # Convertir bytes int16 a numpy float32 normalizado (-1.0 a 1.0)
        audio_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
        if len(audio_int16) == 0:
            return ""

        audio_float32 = audio_int16.astype(np.float32) / 32768.0

        model = self.get_model()
        segments, _ = model.transcribe(
            audio_float32,
            language="es",
            beam_size=1,
            temperature=0.0,
            vad_filter=True,
        )

        transcript_parts = [segment.text.strip() for segment in segments]
        return " ".join(filter(None, transcript_parts))

    @staticmethod
    def pcm_to_wav_bytes(pcm_bytes: bytes, sample_rate: int = 16000) -> bytes:
        """Empaqueta audio PCM 16-bit mono en un archivo WAV en memoria."""
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_bytes)
        return wav_io.getvalue()
