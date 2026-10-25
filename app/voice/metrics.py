import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import numpy as np


@dataclass
class TurnLatency:
    session_id: str
    stt_ms: float
    llm_ms: float
    tts_ms: float
    total_ms: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LatencyMetricsCollector:
    """Recolector de métricas de latencia por etapa para el pipeline de voz."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: list[TurnLatency] = []

    def record_turn(
        self,
        session_id: str,
        stt_ms: float,
        llm_ms: float,
        tts_ms: float,
        total_ms: float,
    ) -> TurnLatency:
        turn = TurnLatency(
            session_id=session_id,
            stt_ms=max(0.0, float(stt_ms)),
            llm_ms=max(0.0, float(llm_ms)),
            tts_ms=max(0.0, float(tts_ms)),
            total_ms=max(0.0, float(total_ms)),
        )
        with self._lock:
            self._records.append(turn)
        return turn

    def get_summary(self) -> dict[str, Any]:
        """Calcula percentiles p50, p90, p95, promedio, mínimo y máximo por etapa."""
        with self._lock:
            records = list(self._records)

        count = len(records)
        if count == 0:
            return {
                "count": 0,
                "stages": {
                    "stt": {"p50": 0.0, "p95": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0},
                    "llm": {"p50": 0.0, "p95": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0},
                    "tts": {"p50": 0.0, "p95": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0},
                    "total": {"p50": 0.0, "p95": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0},
                },
            }

        stt_arr = np.array([r.stt_ms for r in records])
        llm_arr = np.array([r.llm_ms for r in records])
        tts_arr = np.array([r.tts_ms for r in records])
        tot_arr = np.array([r.total_ms for r in records])

        def _stats(arr: np.ndarray) -> dict[str, float]:
            return {
                "p50": round(float(np.percentile(arr, 50)), 2),
                "p90": round(float(np.percentile(arr, 90)), 2),
                "p95": round(float(np.percentile(arr, 95)), 2),
                "mean": round(float(np.mean(arr)), 2),
                "min": round(float(np.min(arr)), 2),
                "max": round(float(np.max(arr)), 2),
            }

        return {
            "count": count,
            "stages": {
                "stt": _stats(stt_arr),
                "llm": _stats(llm_arr),
                "tts": _stats(tts_arr),
                "total": _stats(tot_arr),
            },
        }

    def format_markdown_table(self) -> str:
        """Genera una tabla en formato Markdown con el resumen de métricas p50 y p95."""
        summary = self.get_summary()
        count = summary["count"]
        stages = summary["stages"]

        md = f"### Métricas de Latencia ({count} turnos registrados)\n\n"
        md += "| Etapa | Mínimo (ms) | Promedio (ms) | p50 (ms) | p95 (ms) | Máximo (ms) |\n"
        md += "|---|---|---|---|---|---|\n"

        etiquetas = {
            "stt": "STT (faster-whisper)",
            "llm": "LLM (Inferencia + Tools)",
            "tts": "TTS (Síntesis de voz)",
            "total": "**Punta a Punta (Total)**",
        }

        for key, label in etiquetas.items():
            s = stages.get(key, {})
            md += f"| {label} | {s.get('min', 0.0)} | {s.get('mean', 0.0)} | **{s.get('p50', 0.0)}** | **{s.get('p95', 0.0)}** | {s.get('max', 0.0)} |\n"

        return md

    def clear(self) -> None:
        """Limpia el histórico de métricas recolectadas."""
        with self._lock:
            self._records.clear()


latency_collector = LatencyMetricsCollector()
