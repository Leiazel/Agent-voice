import re
from typing import Any, Callable
from app.llm.base import BaseLLM, LLMResponse, ToolExecution


class MockLLM(BaseLLM):
    """
    Proveedor simulado para pruebas automáticas y ejecución sin conexión.
    Interpreta intenciones comunes para validar el pipeline de agente y herramientas.
    """

    def __init__(self, responses: list[str] | None = None):
        self.responses = list(responses or [])
        self.call_history: list[dict[str, Any]] = []

    def send_message(
        self,
        message: str,
        conversation_history: list[dict[str, str]],
        system_instruction: str,
        tools: list[Callable] | None = None,
    ) -> LLMResponse:
        self.call_history.append({
            "message": message,
            "history": conversation_history,
        })

        if self.responses:
            return LLMResponse(text=self.responses.pop(0), tool_executions=[])

        tool_map = {t.__name__: t for t in (tools or [])}
        tool_executions: list[ToolExecution] = []
        msg_lower = message.lower()

        # Simulación de consulta de alérgenos
        if "alérgeno" in msg_lower or "alergeno" in msg_lower or "gluten" in msg_lower or "lacteos" in msg_lower:
            fn = tool_map.get("tool_consultar_alergenos")
            if fn:
                # Extraer posible plato
                plato = "Risotto de hongos" if "risotto" in msg_lower else "Ensalada Caprese"
                alergeno = "gluten" if "gluten" in msg_lower else ""
                res = fn(nombre_plato=plato, alergeno=alergeno)
                tool_executions.append(
                    ToolExecution(name="tool_consultar_alergenos", args={"nombre_plato": plato, "alergeno": alergeno}, output=res)
                )
                return LLMResponse(text=res["mensaje"], tool_executions=tool_executions)

        # Simulación de disponibilidad
        if "disponibilidad" in msg_lower or "mesa para" in msg_lower or "tienen lugar" in msg_lower:
            fn = tool_map.get("tool_revisar_disponibilidad")
            if fn:
                # Extraer personas y hora si existen
                p_match = re.search(r"(\d+)\s+personas?", msg_lower)
                personas = int(p_match.group(1)) if p_match else 2
                h_match = re.search(r"(\d{2}:\d{2})", message)
                hora = h_match.group(1) if h_match else "20:30"
                fecha = "2026-11-05"
                res = fn(fecha=fecha, hora=hora, personas=personas)
                tool_executions.append(
                    ToolExecution(name="tool_revisar_disponibilidad", args={"fecha": fecha, "hora": hora, "personas": personas}, output=res)
                )
                return LLMResponse(text=res["mensaje"], tool_executions=tool_executions)

        # Simulación de creación de reserva
        if "confirmo" in msg_lower or "si, confirmo" in msg_lower or "crear reserva" in msg_lower:
            fn = tool_map.get("tool_crear_reserva")
            if fn:
                res = fn(nombre="Juan Perez", fecha="2026-11-05", hora="20:30", personas=2)
                tool_executions.append(
                    ToolExecution(name="tool_crear_reserva", args={"nombre": "Juan Perez", "fecha": "2026-11-05", "hora": "20:30", "personas": 2}, output=res)
                )
                return LLMResponse(text=res["mensaje"], tool_executions=tool_executions)

        # Simulación de cancelación
        if "cancelar" in msg_lower:
            id_match = re.search(r"(RES-\d+)", message.upper())
            res_id = id_match.group(1) if id_match else "RES-1001"
            fn = tool_map.get("tool_cancelar_reserva")
            if fn:
                res = fn(id_reserva=res_id)
                tool_executions.append(
                    ToolExecution(name="tool_cancelar_reserva", args={"id_reserva": res_id}, output=res)
                )
                return LLMResponse(text=res["mensaje"], tool_executions=tool_executions)

        # Fuera de alcance
        if "python" in msg_lower or "clima" in msg_lower or "capital" in msg_lower:
            return LLMResponse(
                text="Solo puedo ayudarte con reservas y consultas sobre el restaurante. ¿En qué puedo ayudarte hoy?",
                tool_executions=[]
            )

        # Respuesta genérica
        return LLMResponse(
            text="Buenas tardes, bienvenido a Trattoria Bella Vista. ¿En qué puedo ayudarte hoy con tu reserva?",
            tool_executions=[]
        )
