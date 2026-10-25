from typing import Callable
from app.agent.guardrails import detect_prompt_injection, sanitize_for_speech
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools_adapter import AGENT_TOOLS
from app.llm import BaseLLM, ToolExecution, get_llm_provider


class VoiceReservationAgent:
    """Orquestador conversacional para reservas gastronómicas con guardrails de voz."""

    def __init__(
        self,
        llm: BaseLLM | None = None,
        system_prompt: str = SYSTEM_PROMPT,
        tools: list[Callable] | None = None,
    ):
        self.llm = llm or get_llm_provider()
        self.system_prompt = system_prompt
        self.tools = tools if tools is not None else AGENT_TOOLS
        self.conversation_history: list[dict[str, str]] = []
        self.last_tool_executions: list[ToolExecution] = []

    def reset(self) -> None:
        """Reinicia el historial de la conversación."""
        self.conversation_history = []
        self.last_tool_executions = []

    def process_user_message(self, user_text: str) -> str:
        """
        Procesa el turno conversacional del usuario:
        1. Aplica guardrails de seguridad (inyección de prompt, silencio).
        2. Envía al LLM junto con herramientas y contexto acumulado.
        3. Sanitiza la respuesta para locución limpia y natural (sin markdown).
        4. Actualiza el historial del diálogo.
        """
        texto_limpio = user_text.strip()

        # Guardrail: silencio o mensaje vacío
        if not texto_limpio:
            return "¿Sigues ahí? Por favor dime cómo puedo ayudarte con tu reserva en Trattoria Bella Vista."

        # Guardrail: detección de prompt injection o alteración de directivas
        if detect_prompt_injection(texto_limpio):
            respuesta_segura = (
                "Como asistente de Trattoria Bella Vista, solo puedo ayudarte con reservas "
                "y consultas sobre nuestro menú. ¿En qué fecha te gustaría visitarnos?"
            )
            self._guardar_historial(texto_limpio, respuesta_segura)
            return respuesta_segura

        # Inferencia con LLM y ejecución de herramientas
        try:
            llm_resp = self.llm.send_message(
                message=texto_limpio,
                conversation_history=self.conversation_history,
                system_instruction=self.system_prompt,
                tools=self.tools,
            )
            self.last_tool_executions = llm_resp.tool_executions
            texto_salida = llm_resp.text
        except Exception as e:
            # Manejo resiliente de fallas sin inventar datos
            texto_salida = (
                "Disculpa, tuve un inconveniente técnico temporal al procesar tu solicitud. "
                "Por favor repite tu consulta o comunícate directamente con nuestro restaurante."
            )
            self._guardar_historial(texto_limpio, texto_salida)
            return texto_salida

        # Sanitizar para voz (eliminar cualquier markdown accidental)
        voz_limpia = sanitize_for_speech(texto_salida)
        self._guardar_historial(texto_limpio, voz_limpia)
        return voz_limpia

    def _guardar_historial(self, user_msg: str, model_msg: str) -> None:
        self.conversation_history.append({"role": "user", "content": user_msg})
        self.conversation_history.append({"role": "model", "content": model_msg})
