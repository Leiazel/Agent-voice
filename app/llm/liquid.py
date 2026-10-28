"""Integración con Liquid AI para modelos de decisión (d1, d1.1, d1-ultra)."""

from typing import Any, Callable
import httpx

from app.config import settings
from app.llm.base import BaseLLM, LLMResponse, ToolExecution
from app.logging_config import audit_logger


class LiquidDecisionClient:
    """Cliente para la API de Decision Models de Liquid AI (https://api.liquid.ai)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.liquid_api_key
        self.base_url = (base_url or settings.liquid_base_url).rstrip("/")
        self.model = model or settings.liquid_model

    def evaluate(
        self,
        state: str,
        questions: dict[str, Any],
        timeout: float = 6.0,
    ) -> dict[str, Any]:
        """Envía una evaluación estructurada a /decisions/v1/systemone."""
        if not self.api_key:
            raise ValueError("LIQUID_API_KEY no configurada. Configure LIQUID_API_KEY en .env")

        endpoint = f"{self.base_url}/decisions/v1/systemone"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "state": state,
            "questions": questions,
        }

        with httpx.Client(timeout=timeout) as client:
            resp = client.post(endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()


class LiquidProvider(BaseLLM):
    """
    Proveedor conversacional basado en los modelos de decisión Liquid d1 / d1.1.
    Evalúa intenciones, ejecuta herramientas y genera respuestas estructuradas sin tokens generativos.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.client = LiquidDecisionClient(api_key=api_key, base_url=base_url, model=model)

    def send_message(
        self,
        message: str,
        conversation_history: list[dict[str, str]],
        system_instruction: str,
        tools: list[Callable] | None = None,
    ) -> LLMResponse:
        tool_executions: list[ToolExecution] = []
        state_context = f"Historial reciente: {conversation_history[-2:] if conversation_history else 'inicio'}\nNuevo mensaje: {message}"

        questions = {
            "is_out_of_scope": {
                "type": "noul",
                "instructions": "Is this message completely unrelated to food, menu, opening hours, or restaurant reservations?",
            },
            "intent": {
                "type": "choice",
                "instructions": "¿Cuál es la intención del cliente?",
                "criteria": {
                    "greeting": "El cliente solo saluda, agradece o inicia la conversación",
                    "menu": "El cliente consulta por platos, ingredientes o alérgenos del restaurante",
                    "reservation": "El cliente desea consultar disponibilidad o reservar una mesa",
                    "cancellation": "El cliente desea cancelar una reserva existente",
                    "other": "Cualquier otra consulta",
                },
            },
        }

        try:
            result = self.client.evaluate(state=state_context, questions=questions)
            answers = result.get("answers", {})
            out_of_scope_score = answers.get("is_out_of_scope", {}).get("noul", 0.0)
            intent = answers.get("intent", {}).get("choice", "other")

            if out_of_scope_score > 0.8:
                return LLMResponse(
                    text="Solo puedo responder consultas sobre reservas, horarios y menú de Trattoria Bella Vista.",
                    tool_executions=[],
                )

            if intent == "greeting":
                return LLMResponse(
                    text="¡Hola! Bienvenido a Trattoria Bella Vista. ¿En qué fecha y horario te gustaría reservar una mesa?",
                    tool_executions=[],
                )
            elif intent == "menu":
                return LLMResponse(
                    text="En Trattoria Bella Vista tenemos opciones de pastas, pizzas tradicionales, carnes y postres italianos. ¿Te gustaría conocer los alérgenos de algún plato en particular?",
                    tool_executions=[],
                )
            elif intent in ("reservation", "cancellation"):
                return LLMResponse(
                    text="Con gusto te ayudo con tu reserva. ¿Para cuántas personas, qué día y en qué horario la deseas?",
                    tool_executions=[],
                )
            else:
                return LLMResponse(
                    text="¿En qué puedo ayudarte hoy en Trattoria Bella Vista? Puedes consultarme sobre reservas o nuestro menú.",
                    tool_executions=[],
                )

        except Exception as e:
            audit_logger.error(f"Error en LiquidProvider: {e}")
            raise

