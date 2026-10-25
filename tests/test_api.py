import json
from pathlib import Path
from fastapi.testclient import TestClient

from app.agent.session import session_manager
from app.config import settings
from app.logging_config import CONVERSATIONS_LOG_FILE
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    session_manager.clear()
    settings.llm_provider = "mock"


# ==============================================================================
# TESTS: GET /health
# ==============================================================================

def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "env" in data
    assert "llm_provider" in data
    assert "model" in data


# ==============================================================================
# TESTS: POST /chat y persistencia de sesión
# ==============================================================================

def test_chat_endpoint_saludo_y_tiempos() -> None:
    payload = {"message": "Buenas tardes, ¿cómo están?"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0
    assert "response" in data
    assert "duration_ms" in data
    assert data["duration_ms"] >= 0.0
    assert "Trattoria Bella Vista" in data["response"]


def test_chat_endpoint_flujo_reserva_con_tools() -> None:
    session_id = "test-session-123"

    # Turno 1: Consulta de disponibilidad
    resp1 = client.post(
        "/chat",
        json={"message": "Quisiera reservar una mesa para 2 personas a las 20:30", "session_id": session_id},
    )
    assert resp1.status_code == 200
    d1 = resp1.json()
    assert d1["session_id"] == session_id
    assert len(d1["tools_used"]) == 1
    assert d1["tools_used"][0]["name"] == "tool_revisar_disponibilidad"

    # Turno 2: Confirmación de reserva
    resp2 = client.post(
        "/chat",
        json={"message": "Sí, confirmo la reserva a nombre de Juan Perez", "session_id": session_id},
    )
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert d2["session_id"] == session_id
    assert len(d2["tools_used"]) == 1
    assert d2["tools_used"][0]["name"] == "tool_crear_reserva"
    assert "confirmada" in d2["response"].lower()


def test_chat_reset_session() -> None:
    session_id = "session-to-reset"
    # Crear sesión
    client.post("/chat", json={"message": "Hola", "session_id": session_id})

    # Resetear sesión
    reset_resp = client.post("/chat/reset", json={"session_id": session_id})
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "reset"

    # Segundo reset sobre la misma sesión
    reset_resp_2 = client.post("/chat/reset", json={"session_id": session_id})
    assert reset_resp_2.json()["status"] == "not_found"


# ==============================================================================
# TESTS: Logging estructurado en archivo JSONL
# ==============================================================================

def test_structured_logging_output() -> None:
    test_sid = "audit-test-session"
    client.post("/chat", json={"message": "Quisiera reservar para 2 personas a las 20:30", "session_id": test_sid})

    assert CONVERSATIONS_LOG_FILE.exists()
    
    # Leer última línea del archivo JSONL
    with open(CONVERSATIONS_LOG_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    assert len(lines) > 0
    last_log = json.loads(lines[-1])

    assert "timestamp" in last_log
    assert last_log.get("session_id") == test_sid
    assert "user_message" in last_log
    assert "agent_response" in last_log
    assert "tools_used" in last_log
    assert "duration_ms" in last_log
    assert isinstance(last_log["duration_ms"], (int, float))
