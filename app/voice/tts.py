import io
import wave
from pathlib import Path
from typing import Optional
from app.config import settings


class LocalTTSService:
    """
    Servicio de Text-to-Speech con soporte para Piper y fallback de audio.
    Sintetiza texto plano en audio WAV monoaural.
    """

    def __init__(self, voice_model_path: Optional[str] = None):
        self.voice_model_path = voice_model_path or settings.tts_model
        self._piper_voice = None
        self._tried_loading = False

    def _get_piper(self):
        if self._tried_loading:
            return self._piper_voice

        self._tried_loading = True
        model_file = Path(self.voice_model_path)
        if model_file.exists() and model_file.suffix == ".onnx":
            try:
                import piper
                self._piper_voice = piper.PiperVoice.load(str(model_file))
            except Exception:
                self._piper_voice = None
        return self._piper_voice

    def synthesize_wav_bytes(self, text: str) -> Optional[bytes]:
        """
        Sintetiza texto a bytes de archivo WAV.
        Si hay un modelo Piper local disponible, lo utiliza.
        De lo contrario, retorna None permitiendo que el cliente use síntesis nativa de navegador.
        """
        if not text:
            return None

        voice = self._get_piper()
        if voice is not None:
            wav_io = io.BytesIO()
            with wave.open(wav_io, "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)
            return wav_io.getvalue()

        return None

