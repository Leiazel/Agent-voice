from fastapi.testclient import TestClient
from app.main import app
from app.voice.metrics import LatencyMetricsCollector, latency_collector

client = TestClient(app)


def setup_function() -> None:
    latency_collector.clear()


# ==============================================================================
# TESTS: LatencyMetricsCollector
# ==============================================================================

def test_collector_empty() -> None:
    collector = LatencyMetricsCollector()
    summary = collector.get_summary()
    assert summary["count"] == 0
    assert summary["stages"]["stt"]["p50"] == 0.0
    assert summary["stages"]["total"]["p95"] == 0.0


def test_collector_records_and_percentiles() -> None:
    collector = LatencyMetricsCollector()
    
    # Insertar 10 turnos con valores progresivos
    for i in range(1, 11):
        collector.record_turn(
            session_id=f"test-{i}",
            stt_ms=i * 10,
            llm_ms=i * 20,
            tts_ms=i * 5,
            total_ms=i * 35,
        )

    summary = collector.get_summary()
    assert summary["count"] == 10
    
    # En 10 elementos (10, 20, 30, 40, 50, 60, 70, 80, 90, 100), mediana p50 está entre 50 y 60
    assert 50.0 <= summary["stages"]["stt"]["p50"] <= 60.0
    # p95 es cercano a 95.5
    assert summary["stages"]["stt"]["p95"] > 80.0
    assert summary["stages"]["total"]["max"] == 350.0
    assert summary["stages"]["total"]["min"] == 35.0


def test_collector_markdown_formatting() -> None:
    collector = LatencyMetricsCollector()
    collector.record_turn(session_id="s1", stt_ms=30.0, llm_ms=100.0, tts_ms=20.0, total_ms=150.0)
    
    table_md = collector.format_markdown_table()
    assert "Métricas de Latencia (1 turnos registrados)" in table_md
    assert "| STT (faster-whisper) |" in table_md
    assert "| **Punta a Punta (Total)** |" in table_md
    assert "p50 (ms)" in table_md
    assert "p95 (ms)" in table_md


# ==============================================================================
# TESTS: Endpoints HTTP de Métricas de Latencia
# ==============================================================================

def test_get_metrics_latency_endpoint() -> None:
    # Registrar un par de turnos en el colector global
    latency_collector.record_turn(session_id="ep1", stt_ms=25.0, llm_ms=50.0, tts_ms=10.0, total_ms=85.0)

    resp = client.get("/metrics/latency")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert "stages" in data
    assert data["stages"]["stt"]["p50"] == 25.0
    assert data["stages"]["total"]["p50"] == 85.0


def test_get_metrics_table_endpoint() -> None:
    latency_collector.record_turn(session_id="ep2", stt_ms=20.0, llm_ms=40.0, tts_ms=10.0, total_ms=70.0)

    resp = client.get("/metrics/latency/table")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    assert "Métricas de Latencia" in resp.text
    assert "p50 (ms)" in resp.text


def test_reset_metrics_endpoint() -> None:
    latency_collector.record_turn(session_id="ep3", stt_ms=10.0, llm_ms=10.0, tts_ms=10.0, total_ms=30.0)
    assert latency_collector.get_summary()["count"] == 1

    reset_resp = client.post("/metrics/latency/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "cleared"

    assert latency_collector.get_summary()["count"] == 0
