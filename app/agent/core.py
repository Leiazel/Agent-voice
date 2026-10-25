from typing import Callable
from app.agent.guardrails import (
    detect_out_of_scope,
    detect_prompt_injection,
    is_unintelligible,
    sanitize_for_speech,
)
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools_adapter import AGENT_TOOLS
from app.llm import BaseLLM, ToolExecution, get_llm_provider


class VoiceReservationAgent:
    """Orquestador conversacional para reservas gastronómicas con guardrails completos."""

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
        self._consecutive_silence: int = 0
        self._consecutive_misunderstanding: int = 0

    def reset(self) -> None:
        """Reinicia el historial y los contadores de la conversación."""
        self.conversation_history = []
        self.last_tool_executions = []
        self._consecutive_silence = 0
        self._consecutive_misunderstanding = 0

    def process_user_message(self, user_text: str) -> str:
        """
        Procesa el turno conversacional del usuario aplicando guardrails exhaustivos:
        1. Guardrail de silencio con política de cierre tras 2 silencios.
        2. Guardrail de ininteligibilidad con política de 2 intentos antes de derivar a teléfono.
        3. Guardrail de protección contra Prompt Injection / Jailbreaks.
        4. Guardrail de rechazo para solicitudes fuera de alcance.
        5. Llamada segura al LLM y herramientas con manejo de excepciones.
        6. Sanitización para voz limpia.
        """
        texto_limpio = user_text.strip()

        # 1. Guardrail: Silencio prolongado (2 intentos)
        if not texto_limpio:
            self._consecutive_silence += 1
            if self._consecutive_silence == 1:
                return "¿Sigues ahí? Por favor dime cómo puedo ayudarte con tu reserva en Trattoria Bella Vista."
            else:
                return "Dado que no recibo respuesta, daré por finalizada la llamada. ¡Gracias por comunicarte con Trattoria Bella Vista!"

        self._consecutive_silence = 0

        # 2. Guardrail: Entendimiento / Ruido ininteligible (2 intentos fallidos)
        if is_unintelligible(texto_limpio):
            self._consecutive_misunderstanding += 1
            if self._consecutive_misunderstanding == 1:
                respuesta = "Disculpa, no logré entenderte bien. ¿Podrías repetirme tu consulta o qué día te gustaría reservar?"
            else:
                respuesta = (
                    "Sigo sin poder comprender tu mensaje. Para ayudarte mejor, "
                    "por favor comunícate por teléfono con el restaurante al 11-4567-8900 o reserva desde nuestra página web."
                )
            self._guardar_historial(texto_limpio, respuesta)
            return respuesta

        self._consecutive_misunderstanding = 0

        # 3. Guardrail: Prompt Injection / Jailbreak
        if detect_prompt_injection(texto_limpio):
            respuesta_segura = (
                "Como asistente de Trattoria Bella Vista, solo puedo ayudarte con reservas "
                "y consultas sobre nuestro restaurante. ¿En qué fecha te gustaría visitarnos?"
            )
            self._guardar_historial(texto_limpio, respuesta_segura)
            return respuesta_segura

        # 4. Guardrail: Solicitudes fuera de alcance
        if detect_out_of_scope(texto_limpio):
            respuesta_alcance = (
                "Solo puedo responder sobre reservas, horarios y el menú de Trattoria Bella Vista. "
                "¿Deseas consultar disponibilidad para alguna fecha?"
            )
            self._guardar_historial(texto_limpio, respuesta_alcance)
            return respuesta_alcance

        # 5. Inferencia con LLM y herramientas
        try:
            llm_resp = self.llm.send_message(
                message=texto_limpio,
                conversation_history=self.conversation_history,
                system_instruction=self.system_prompt,
                tools=self.tools,
            )
            self.last_tool_executions = llm_resp.tool_executions
            texto_salida = llm_resp.text
        except Exception:
            texto_salida = (
                "Disculpa, tuve un inconveniente técnico temporal al procesar tu solicitud. "
                "Por favor repite tu consulta o comunícate directamente con nuestro restaurante."
            )
            self._guardar_historial(texto_limpio, texto_salida)
            return texto_salida

        # 6. Sanitizar formato para voz
        voz_limpia = sanitize_for_speech(texto_salida)
        self._guardar_historial(texto_limpio, voz_limpia)
        return voz_limpia

    def _guardar_historial(self, user_msg: str, model_msg: str) -> None:
        self.conversation_history.append({"role": "user", "content": user_msg})
        self.conversation_history.append({"role": "model", "content": model_msg})
