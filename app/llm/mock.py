import re
import unicodedata
from datetime import date, timedelta
from typing import Any, Callable
from app.config import settings
from app.llm.base import BaseLLM, LLMResponse, ToolExecution
from app.tools.menu import cargar_menu


class MockLLM(BaseLLM):
    """
    Proveedor simulado e inteligente para pruebas, benchmarking y evaluación offline.
    Extrae argumentos de las peticiones para invocar herramientas reales sin llamadas de red.
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
        msg_lower = message.lower().strip()
        msg_norm = "".join(
            c for c in unicodedata.normalize("NFD", msg_lower)
            if unicodedata.category(c) != "Mn"
        )

        # Acumular contexto de la conversación para extraer datos de turnos previos
        full_context = " ".join([turn.get("content", "") for turn in conversation_history]) + " " + message
        full_lower = full_context.lower()
        full_norm = "".join(
            c for c in unicodedata.normalize("NFD", full_lower)
            if unicodedata.category(c) != "Mn"
        )

        # 1. Herramienta: Cancelar reserva
        # Se activa si el mensaje actual pide cancelar, o si hay un ID de reserva en contexto de cancelación
        quiere_cancelar = (
            "cancel" in msg_norm
            or (re.search(r"RES-\d+", message, re.IGNORECASE) and "cancel" in full_norm)
        )
        if quiere_cancelar:
            fn = tool_map.get("tool_cancelar_reserva")
            if fn:
                id_match = re.search(r"(RES-\d+)", message, re.IGNORECASE) or re.search(r"(RES-\d+)", full_context, re.IGNORECASE)
                if id_match:
                    res_id = id_match.group(1).upper()
                    res = fn(id_reserva=res_id)
                    tool_executions.append(
                        ToolExecution(name="tool_cancelar_reserva", args={"id_reserva": res_id}, output=res)
                    )
                    return LLMResponse(text=res["mensaje"], tool_executions=tool_executions)

        # 2. Herramienta: Consultar alérgenos
        quiere_alergenos = (
            "alergen" in msg_norm
            or "alergia" in msg_norm
            or any(a in msg_norm for a in (
                "gluten", "lacteo", "nuez", "nueces", "pescado", "fruto seco",
                "frutos secos", "frutos_secos", "huevo", "trigo", "tacc", "celiaco"
            ))
        )
        if quiere_alergenos:
            fn = tool_map.get("tool_consultar_alergenos")
            if fn:
                platos = cargar_menu()
                mejor_plato = None
                max_coincidencias = 0
                for p in platos:
                    nombre_p = p["nombre"]
                    palabras = [w for w in re.findall(r"\w+", nombre_p.lower()) if len(w) > 3 and w not in ("salsa", "sabor", "tipo")]
                    coincidencias = sum(1 for w in palabras if w in msg_lower)
                    if coincidencias > max_coincidencias:
                        max_coincidencias = coincidencias
                        mejor_plato = nombre_p

                if not mejor_plato:
                    if "taco" in msg_lower:
                        mejor_plato = "Tacos de asado"
                    elif "pizza" in msg_lower:
                        mejor_plato = "Pizza napolitana"
                    else:
                        match = re.search(r"(?:en|de|del|los|el|la)\s+([A-Za-zñáéíóúÁÉÍÓÚ\s]{3,20})", message)
                        mejor_plato = match.group(1).strip() if match else "Risotto de hongos"

                # Extraer alérgeno consultado
                alergeno = ""
                if any(w in msg_norm for w in ("frutos secos", "frutos_secos", "nuez", "nueces", "almendra", "pistacho")):
                    alergeno = "frutos_secos"
                elif any(w in msg_norm for w in ("gluten", "trigo", "tacc", "harina", "celiaco")):
                    alergeno = "gluten"
                elif any(w in msg_norm for w in ("lacteo", "leche", "queso", "crema", "manteca", "ricota")):
                    # Si no consultó frutos secos o gluten específicamente pero menciona ricota
                    if not alergeno:
                        alergeno = "lacteos"
                elif any(w in msg_norm for w in ("pescado", "salmon", "atun")):
                    alergeno = "pescado"
                elif any(w in msg_norm for w in ("huevo", "huevos")):
                    alergeno = "huevo"
                elif any(w in msg_norm for w in ("marisco", "mariscos", "camaron")):
                    alergeno = "mariscos"
                elif any(w in msg_norm for w in ("soja", "soya")):
                    alergeno = "soja"

                res = fn(nombre_plato=mejor_plato, alergeno=alergeno)
                tool_executions.append(
                    ToolExecution(name="tool_consultar_alergenos", args={"nombre_plato": mejor_plato, "alergeno": alergeno}, output=res)
                )
                return LLMResponse(text=res["mensaje"], tool_executions=tool_executions)

        # 3. Herramienta: Crear reserva (confirmación explícita)
        es_confirmacion = any(
            w in msg_norm for w in (
                "confirmo", "confirmar", "confirmame", "confirmo la reserva",
                "si, confirmo", "dale, confirmo", "perfecto, confirmo", "de acuerdo, confirmo"
            )
        )
        if es_confirmacion:
            fn = tool_map.get("tool_crear_reserva")
            if fn:
                # Extraer nombre
                nombre = "Cliente Ficticio"
                nom_match = re.search(r"(?:a nombre de|para|soy)\s+([A-Za-zñáéíóúÁÉÍÓÚ\s]{3,35})", message, re.IGNORECASE)
                if nom_match:
                    nombre = nom_match.group(1).strip()
                    for stop_word in ("por favor", "gracias", "muchas gracias", "a las"):
                        if stop_word in nombre.lower():
                            nombre = re.split(re.escape(stop_word), nombre, flags=re.IGNORECASE)[0].strip()
                elif "juan perez" in full_lower:
                    nombre = "Juan Perez"
                elif "maria gomez" in full_lower:
                    nombre = "Maria Gomez"

                # Extraer fecha
                fecha_match = re.search(r"(\d{4}-\d{2}-\d{2})", full_context)
                fecha = fecha_match.group(1) if fecha_match else "2026-11-05"

                # Extraer hora
                hora_match = re.search(r"(\d{1,2}:\d{2})", full_context)
                hora = hora_match.group(1) if hora_match else "20:30"
                if len(hora.split(":")[0]) == 1:
                    hora = "0" + hora

                # Extraer personas
                p_match = re.search(r"(\d+)\s*(?:personas?|comensales?)", full_context, re.IGNORECASE)
                personas = int(p_match.group(1)) if p_match else 2

                res = fn(nombre=nombre, fecha=fecha, hora=hora, personas=personas)
                tool_executions.append(
                    ToolExecution(name="tool_crear_reserva", args={"nombre": nombre, "fecha": fecha, "hora": hora, "personas": personas}, output=res)
                )
                return LLMResponse(text=res["mensaje"], tool_executions=tool_executions)

        # 4. Herramienta: Revisar disponibilidad
        es_disponibilidad = (
            not es_confirmacion
            and (
                any(w in msg_norm for w in (
                    "disponib", "reserva", "reservar", "mesa", "lugar", "tienen",
                    "comensal", "cenar", "almorzar", "almuerzo", "cena"
                ))
                or bool(re.search(r"\d{1,2}:\d{2}", message))
                or bool(re.search(r"\d+\s*personas?", msg_lower))
            )
        )
        if es_disponibilidad:
            fn = tool_map.get("tool_revisar_disponibilidad")
            if fn:
                # Extraer fecha
                fecha_match = re.search(r"(\d{4}-\d{2}-\d{2})", full_context)
                if fecha_match:
                    fecha = fecha_match.group(1)
                elif "hoy" in full_lower or "viernes" in full_lower:
                    fecha = "2026-11-05"
                else:
                    fecha = "2026-11-05"

                # Extraer hora (priorizar hora del mensaje actual si existe)
                h_match = re.search(r"(\d{1,2}:\d{2})", message) or re.search(r"(\d{1,2}:\d{2})", full_context)
                hora = h_match.group(1) if h_match else "20:30"
                if len(hora.split(":")[0]) == 1:
                    hora = "0" + hora

                # Extraer personas (priorizar mensaje actual si existe)
                p_match = re.search(r"(\d+)\s*(?:personas?|comensales?)", message, re.IGNORECASE)
                if not p_match:
                    p_match = re.search(r"(\d+)\s*(?:personas?|comensales?)", full_context, re.IGNORECASE)

                if p_match:
                    personas = int(p_match.group(1))
                elif "una sola persona" in full_lower or "1 persona" in full_lower:
                    personas = 1
                else:
                    somos_match = (
                        re.search(r"(?:somos|para)\s+(\d+)", message, re.IGNORECASE)
                        or re.search(r"(?:somos|para)\s+(\d+)", full_context, re.IGNORECASE)
                    )
                    personas = int(somos_match.group(1)) if somos_match else 2

                res = fn(fecha=fecha, hora=hora, personas=personas)
                tool_executions.append(
                    ToolExecution(name="tool_revisar_disponibilidad", args={"fecha": fecha, "hora": hora, "personas": personas}, output=res)
                )
                return LLMResponse(text=res["mensaje"], tool_executions=tool_executions)

        # 5. Respuestas de diálogo general
        if "horario" in msg_lower or "turnos" in msg_lower:
            return LLMResponse(
                text="Abrimos para almuerzo de 12:00 a 15:30 y para cena de 20:00 a 23:30 con turnos cada 30 minutos.",
                tool_executions=[]
            )

        if "cancel" in msg_norm:
            return LLMResponse(
                text="Con gusto te ayudo a cancelar tu reserva. Por favor indícame el código identificador de tu reserva.",
                tool_executions=[]
            )

        # Fuera de alcance
        if any(w in msg_lower for w in ("python", "script", "programar", "clima", "capital de", "bitcoin", "elecciones", "partido de")):
            return LLMResponse(
                text="Solo puedo ayudarte con reservas y consultas sobre el restaurante. ¿En qué puedo ayudarte hoy?",
                tool_executions=[]
            )

        # Bienvenida por defecto
        return LLMResponse(
            text="Buenas tardes, bienvenido a Trattoria Bella Vista. ¿En qué fecha y horario te gustaría reservar?",
            tool_executions=[]
        )
