import json
import numpy as np
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.voice.stt import FasterWhisperSTT
from app.voice.tts import LocalTTSService
from app.voice.vad import SileroVoiceDetector

client = TestClient(app)


def setup_function() -> None:
    settings.llm_provider = "mock"


# ==============================================================================
# TESTS: Componentes de Voz (VAD, STT, TTS)
# ==============================================================================

def test_silero_vad_silence_detection() -> None:
    vad = SileroVoiceDetector(confidence_threshold=0.5)
    
    # Audio vacío
    assert vad.voice_confidence(b"") == 0.0
    assert vad.is_speech(b"") is False

    # 512 muestras de silencio (1024 bytes int16)
    silence = np.zeros(512, dtype=np.int16).tobytes()
    conf = vad.voice_confidence(silence)
    assert conf < 0.1
    assert vad.is_speech(silence) is False


def test_faster_whisper_stt_empty_and_wav_generation() -> None:
    stt = FasterWhisperSTT(model_name="tiny")
    
    # Bytes vacíos retornan cadena vacía
    assert stt.transcribe_audio_bytes(b"") == ""

    # Empaquetado WAV
    dummy_pcm = np.zeros(16000, dtype=np.int16).tobytes()
    wav_bytes = stt.pcm_to_wav_bytes(dummy_pcm)
    assert wav_bytes.startswith(b"RIFF")
    assert b"WAVE" in wav_bytes[:16]


def test_local_tts_empty_input() -> None:
    tts = LocalTTSService(voice_model_path="non_existent.onnx")
    assert tts.synthesize_wav_bytes("") is None


# ==============================================================================
# TESTS: Endpoint Web y WebSocket
# ==============================================================================

def test_index_ui_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Trattoria Bella Vista" in response.text
    assert "Iniciar Llamada" in response.text
    assert "/ws/voice" in response.text


def test_voice_websocket_handshake_and_control() -> None:
    with client.websocket_connect("/ws/voice") as websocket:
        # Mensajes iniciales de bienvenida emitidos al conectar (transcript, status speaking, speech/audio)
        init_msgs = [json.loads(websocket.receive_text()) for _ in range(3)]
        init_types = [m["type"] for m in init_msgs]
        assert "transcript" in init_types
        assert "status" in init_types
        assert any(t in ("speech", "audio") for t in init_types)

        # Probar ping - pong
        websocket.send_text(json.dumps({"type": "ping"}))
        pong = json.loads(websocket.receive_text())
        assert pong["type"] == "pong"

        # Probar interacción por texto a través del WebSocket
        websocket.send_text(json.dumps({
            "type": "text_input",
            "text": "Quisiera reservar una mesa para 2 personas a las 20:30"
        }))

        received_types = []
        for _ in range(3):
            data = json.loads(websocket.receive_text())
            received_types.append(data["type"])

        assert "status" in received_types
        assert "transcript" in received_types
