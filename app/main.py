import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Optional
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

from app.agent.session import session_manager
from app.config import settings
from app.logging_config import audit_logger
from app.voice import FasterWhisperSTT, latency_collector
from app.voice.pipeline import VoiceSession


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Ciclo de vida de la aplicación: pre-calentamiento de modelos en memoria."""
    audit_logger.info("Iniciando servidor y precargando modelo Whisper STT...")
    try:
        FasterWhisperSTT().get_model()
    except Exception as e:
        audit_logger.warning(f"No se pudo precargar Whisper STT: {e}")
    yield


app = FastAPI(
    title="Restaurant Voice Agent",
    description="Backend FastAPI para atención conversacional y reservas con IA",
    version="0.1.0",
    lifespan=lifespan,
)


class HealthResponse(BaseModel):
    status: str
    env: str
    llm_provider: str
    model: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje del usuario")
    session_id: Optional[str] = Field(default=None, description="Identificador único de la sesión (opcional)")


class ToolExecutionDto(BaseModel):
    name: str
    args: dict[str, Any]
    output: Any


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tools_used: list[ToolExecutionDto] = Field(default_factory=list)
    duration_ms: float


class ResetSessionRequest(BaseModel):
    session_id: str


@app.get("/", response_class=HTMLResponse, tags=["UI"])
def index() -> HTMLResponse:
    """Sirve la interfaz web para interactuar con el agente por voz."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if not template_path.exists():
        return HTMLResponse("<h1>Trattoria Bella Vista - Interfaz no encontrada</h1>", status_code=404)
    return HTMLResponse(template_path.read_text(encoding="utf-8"))


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    """Retorna el favicon oficial para evitar errores 404 en la consola."""
    icon_path = Path(__file__).resolve().parent.parent / "icon.svg"
    if icon_path.exists():
        return Response(content=icon_path.read_bytes(), media_type="image/svg+xml")
    return Response(status_code=204)


@app.websocket("/ws/voice")
async def voice_websocket_endpoint(websocket: WebSocket) -> None:
    """Endpoint WebSocket para streaming de voz bidireccional y barge-in."""
    session_id = str(uuid.uuid4())
    session = VoiceSession(websocket=websocket, session_id=session_id)
    await session.run()


@app.get("/metrics/latency", tags=["Métricas"])
def get_latency_metrics() -> dict[str, Any]:
    """Retorna las métricas de latencia acumuladas con percentiles p50, p90 y p95 por etapa."""
    return latency_collector.get_summary()


@app.get("/metrics/latency/table", response_class=PlainTextResponse, tags=["Métricas"])
def get_latency_markdown_table() -> PlainTextResponse:
    """Retorna las métricas de latencia en formato de tabla Markdown."""
    return PlainTextResponse(latency_collector.format_markdown_table())


@app.post("/metrics/latency/reset", tags=["Métricas"])
def reset_latency_metrics() -> dict[str, str]:
    """Reinicia las métricas de latencia registradas."""
    latency_collector.clear()
    return {"status": "cleared"}


@app.get("/health", response_model=HealthResponse, tags=["Salud"])
def health_check() -> HealthResponse:
    """Verifica el estado del servicio y la configuración activa del LLM."""
    if settings.llm_provider == "gemini":
        model_name = settings.gemini_model
    elif settings.llm_provider in ("openai", "groq", "openrouter"):
        model_name = settings.openai_model
    elif settings.llm_provider == "liquid":
        model_name = settings.liquid_model
    else:
        model_name = settings.ollama_model
    return HealthResponse(
        status="ok",
        env=settings.app_env,
        llm_provider=settings.llm_provider,
        model=model_name,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Conversación"])
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """Procesa un turno conversacional, ejecuta herramientas y registra tiempos y auditoría."""
    start_time = time.perf_counter()

    try:
        session_id, agent = session_manager.get_or_create(payload.session_id)
        agent_reply = agent.process_user_message(payload.message)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Mapeo de herramientas ejecutadas
        tools_executed = [
            ToolExecutionDto(name=te.name, args=te.args, output=te.output)
            for te in agent.last_tool_executions
        ]

        # Logging estructurado por turno de conversación
        audit_logger.info(
            f"Conversación procesada [{session_id}] en {duration_ms} ms",
            extra={
                "session_id": session_id,
                "user_message": payload.message,
                "agent_response": agent_reply,
                "tools_used": [te.model_dump() for te in tools_executed],
                "duration_ms": duration_ms,
            },
        )

        return ChatResponse(
            session_id=session_id,
            response=agent_reply,
            tools_used=tools_executed,
            duration_ms=duration_ms,
        )

    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        audit_logger.error(
            f"Error procesando conversación: {exc}",
            extra={
                "session_id": payload.session_id or "unknown",
                "user_message": payload.message,
                "error": str(exc),
                "duration_ms": duration_ms,
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Error interno procesando la solicitud conversacional.",
        )


@app.post("/chat/reset", tags=["Conversación"])
def reset_session(payload: ResetSessionRequest) -> dict[str, str]:
    """Reinicia el estado y memoria de una conversación."""
    removed = session_manager.remove(payload.session_id)
    return {
        "session_id": payload.session_id,
        "status": "reset" if removed else "not_found",
    }
