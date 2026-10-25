import base64
import json
import time
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect

from app.agent.core import VoiceReservationAgent
from app.logging_config import audit_logger
from app.voice.stt import FasterWhisperSTT
from app.voice.tts import LocalTTSService
from app.voice.vad import SileroVoiceDetector


class VoiceSession:
    """Sesión de voz interactiva en tiempo real sobre WebSocket con VAD, STT, LLM, TTS y barge-in."""

    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.agent = VoiceReservationAgent()
        self.vad = SileroVoiceDetector(sample_rate=16000, confidence_threshold=0.45)
        self.stt = FasterWhisperSTT()
        self.tts = LocalTTSService()

        self._audio_buffer = bytearray()
        self._speech_buffer = bytearray()
        self._is_speaking = False
        self._is_bot_speaking = False
        self._silence_frames_count = 0
        self._silence_threshold_frames = 15  # ~480ms de silencio para marcar fin de turno

    async def run(self) -> None:
        """Loop principal de atención por WebSocket."""
        await self.websocket.accept()
        audit_logger.info(f"Cliente de voz conectado [{self.session_id}]")
        
        # Enviar estado inicial y saludo del agente
        saludo = "Buenas tardes, bienvenido a Trattoria Bella Vista. ¿En qué fecha y horario te gustaría reservar?"
        await self._send_json({
            "type": "transcript",
            "role": "assistant",
            "text": saludo,
        })
        await self._synthesize_and_stream(saludo)

        try:
            while True:
                message = await self.websocket.receive()
                
                # Tráfico de audio binario (PCM 16kHz mono)
                if "bytes" in message and message["bytes"]:
                    await self._handle_audio_chunk(message["bytes"])
                
                # Tráfico de control de texto JSON
                elif "text" in message and message["text"]:
                    await self._handle_text_control(message["text"])

        except WebSocketDisconnect:
            audit_logger.info(f"Cliente de voz desconectado [{self.session_id}]")
        except Exception as e:
            audit_logger.error(f"Error en sesión de voz [{self.session_id}]: {e}")

    async def _handle_audio_chunk(self, chunk: bytes) -> None:
        """Procesa fragmentos de audio entrantes con Silero VAD y detecta barge-in."""
        self._audio_buffer.extend(chunk)

        # Procesar en ventanas de 1024 bytes (512 muestras de 16-bit a 16kHz = 32ms)
        while len(self._audio_buffer) >= 1024:
            window = bytes(self._audio_buffer[:1024])
            del self._audio_buffer[:1024]

            is_voice = self.vad.is_speech(window)

            # 1. Detección de Barge-in (Interrupción del usuario mientras el agente habla)
            if is_voice and self._is_bot_speaking:
                self._is_bot_speaking = False
                await self._send_json({
                    "type": "interruption",
                    "message": "barge-in detectado",
                })
                audit_logger.info(f"Barge-in detectado en sesión [{self.session_id}]")

            # 2. Detección de inicio de habla del usuario
            if is_voice:
                self._silence_frames_count = 0
                self._speech_buffer.extend(window)
                if not self._is_speaking:
                    self._is_speaking = True
                    await self._send_json({"type": "status", "state": "listening"})
            else:
                # 3. Detección de silencio continuo para cerrar turno
                if self._is_speaking:
                    self._speech_buffer.extend(window)
                    self._silence_frames_count += 1

                    if self._silence_frames_count >= self._silence_threshold_frames:
                        self._is_speaking = False
                        self._silence_frames_count = 0
                        await self._process_turn_end()

    async def _process_turn_end(self) -> None:
        """Finaliza el turno de habla del usuario, ejecuta STT, LLM y responde."""
        pcm_data = bytes(self._speech_buffer)
        self._speech_buffer.clear()

        # Descartar ruidos ultra cortos (< 300ms de audio)
        if len(pcm_data) < 16000 * 2 * 0.3:
            return

        t_vad_end = time.perf_counter()
        await self._send_json({"type": "status", "state": "thinking"})

        # STT con faster-whisper
        t_stt_start = time.perf_counter()
        user_transcript = self.stt.transcribe_audio_bytes(pcm_data)
        t_stt_done = time.perf_counter()

        if not user_transcript.strip():
            await self._send_json({"type": "status", "state": "listening"})
            return

        await self._send_json({
            "type": "transcript",
            "role": "user",
            "text": user_transcript,
        })

        # LLM + Herramientas de negocio
        t_llm_start = time.perf_counter()
        agent_reply = self.agent.process_user_message(user_transcript)
        t_llm_done = time.perf_counter()

        # Notificar herramientas ejecutadas
        for te in self.agent.last_tool_executions:
            await self._send_json({
                "type": "tool_executed",
                "name": te.name,
                "args": te.args,
            })

        await self._send_json({
            "type": "transcript",
            "role": "assistant",
            "text": agent_reply,
        })

        # TTS + Streaming de audio
        t_tts_start = time.perf_counter()
        await self._synthesize_and_stream(agent_reply)
        t_tts_done = time.perf_counter()

        # Métricas de latencia de la etapa
        stt_ms = round((t_stt_done - t_stt_start) * 1000, 2)
        llm_ms = round((t_llm_done - t_llm_start) * 1000, 2)
        tts_ms = round((t_tts_done - t_tts_start) * 1000, 2)
        total_ms = round((t_tts_done - t_vad_end) * 1000, 2)

        metrics = {
            "stt_ms": stt_ms,
            "llm_ms": llm_ms,
            "tts_ms": tts_ms,
            "total_ms": total_ms,
        }
        await self._send_json({"type": "metrics", "data": metrics})

        audit_logger.info(
            f"Turno de voz [{self.session_id}]: STT={stt_ms}ms, LLM={llm_ms}ms, TTS={tts_ms}ms | Total={total_ms}ms"
        )

    async def _synthesize_and_stream(self, text: str) -> None:
        """Sintetiza la respuesta y emite audio o directiva de locución."""
        self._is_bot_speaking = True
        await self._send_json({"type": "status", "state": "speaking"})

        wav_bytes = self.tts.synthesize_wav_bytes(text)
        if wav_bytes:
            audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")
            await self._send_json({
                "type": "audio",
                "data": audio_b64,
            })
        else:
            # Si no hay binario de modelo Piper, envía evento de síntesis para el Web Speech API del navegador
            await self._send_json({
                "type": "speech",
                "text": text,
            })

    async def _handle_text_control(self, raw_json: str) -> None:
        """Maneja mensajes de control JSON enviados por el cliente."""
        try:
            data = json.loads(raw_json)
            msg_type = data.get("type")

            if msg_type == "bot_playback_finished":
                self._is_bot_speaking = False
                await self._send_json({"type": "status", "state": "listening"})

            elif msg_type == "text_input":
                user_text = data.get("text", "").strip()
                if user_text:
                    await self._send_json({"type": "status", "state": "thinking"})
                    await self._send_json({"type": "transcript", "role": "user", "text": user_text})
                    reply = self.agent.process_user_message(user_text)
                    await self._send_json({"type": "transcript", "role": "assistant", "text": reply})
                    await self._synthesize_and_stream(reply)

            elif msg_type == "ping":
                await self._send_json({"type": "pong"})

        except json.JSONDecodeError:
            pass

    async def _send_json(self, payload: dict[str, Any]) -> None:
        try:
            await self.websocket.send_text(json.dumps(payload, ensure_ascii=False))
        except Exception:
            pass
