#!/usr/bin/env python3
"""
Script de benchmarking de latencia para el pipeline de voz.
Mide y reporta percentiles p50 y p95 por etapa (STT, LLM, TTS y Total).
"""

import json
import time
from pathlib import Path
import numpy as np

from app.agent.core import VoiceReservationAgent
from app.config import settings
from app.voice.metrics import LatencyMetricsCollector
from app.voice.stt import FasterWhisperSTT
from app.voice.tts import LocalTTSService

RESULTS_DIR = Path("eval/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_MD_FILE = RESULTS_DIR / "latency_benchmark.md"
REPORT_JSON_FILE = RESULTS_DIR / "latency_benchmark.json"

TEST_UTTERANCES = [
    "Hola, buenas tardes",
    "Quisiera saber si tienen disponibilidad para 2 personas el viernes a las 20:30",
    "¿Qué opciones de principales tienen?",
    "¿El Risotto de hongos tiene lácteos?",
    "¿La Ensalada Caprese tiene gluten?",
    "Confirmo la reserva para 2 personas el 2026-11-05 a las 20:30 a nombre de Sofia Rossi",
    "Quiero cancelar la reserva RES-1001",
    "¿Tienen mesas para 4 personas a las 13:00?",
    "¿Cuál es el horario de atención para cenar?",
    "Muchas gracias por la atención, hasta luego",
]


def run_benchmark(num_iterations: int = 2) -> dict:
    print("=" * 70)
    print("  BENCHMARK DE LATENCIA POR ETAPA (Fase 6)")
    print(f"  Proveedor LLM: {settings.llm_provider}")
    print(f"  Modelo STT: faster-whisper ({settings.stt_model})")
    print(f"  Total de turnos de prueba: {len(TEST_UTTERANCES) * num_iterations}")
    print("=" * 70)

    collector = LatencyMetricsCollector()
    stt = FasterWhisperSTT()
    agent = VoiceReservationAgent()
    tts = LocalTTSService()

    # Pre-calentamiento de modelos
    print("\n[1/3] Pre-calentando modelos en memoria...")
    stt.get_model()
    dummy_audio = np.zeros(16000 * 2, dtype=np.int16).tobytes()
    stt.transcribe_audio_bytes(dummy_audio)

    print("[2/3] Ejecutando turnos conversacionales con medición de tiempos...")
    turn_idx = 0
    for iteration in range(num_iterations):
        for phrase in TEST_UTTERANCES:
            turn_idx += 1
            session_id = f"bench-turn-{turn_idx}"

            # 1. Simulación y medición de STT
            # Generar buffer PCM con tono/ruido simulado equivalente a la frase
            duration_secs = max(1.0, len(phrase) * 0.05)
            num_samples = int(16000 * duration_secs)
            pcm_buffer = (np.random.randn(num_samples) * 500).astype(np.int16).tobytes()

            t0 = time.perf_counter()
            # Medimos la llamada al motor Whisper
            stt.transcribe_audio_bytes(pcm_buffer)
            t_stt = time.perf_counter()
            stt_ms = round((t_stt - t0) * 1000, 2)

            # 2. Medición de LLM + Herramientas
            t_llm_start = time.perf_counter()
            reply = agent.process_user_message(phrase)
            t_llm_done = time.perf_counter()
            llm_ms = round((t_llm_done - t_llm_start) * 1000, 2)

            # 3. Medición de TTS
            t_tts_start = time.perf_counter()
            tts.synthesize_wav_bytes(reply)
            t_tts_done = time.perf_counter()
            tts_ms = round((t_tts_done - t_tts_start) * 1000, 2)

            total_ms = round(stt_ms + llm_ms + tts_ms, 2)

            collector.record_turn(
                session_id=session_id,
                stt_ms=stt_ms,
                llm_ms=llm_ms,
                tts_ms=tts_ms,
                total_ms=total_ms,
            )
            print(f"  Turno {turn_idx:02d}: STT={stt_ms:6.1f}ms | LLM={llm_ms:6.1f}ms | TTS={tts_ms:5.1f}ms | Total={total_ms:6.1f}ms -> '{phrase[:35]}...'")

    print("\n[3/3] Calculando percentiles p50 y p95...")
    summary = collector.get_summary()
    md_table = collector.format_markdown_table()

    # Guardar reportes
    with open(REPORT_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(REPORT_MD_FILE, "w", encoding="utf-8") as f:
        f.write("# Reporte de Benchmark de Latencia\n\n")
        f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"- Proveedor LLM: `{settings.llm_provider}`\n")
        f.write(f"- Modelo STT: `faster-whisper ({settings.stt_model})`\n\n")
        f.write(md_table)

    print("\n" + md_table)
    print(f"Reporte guardado en: {REPORT_MD_FILE}")
    return summary


if __name__ == "__main__":
    run_benchmark()
