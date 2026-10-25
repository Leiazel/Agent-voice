"""Adaptadores de herramientas para ser consumidos por los LLMs (Gemini, Ollama)."""

from typing import Any
from app.tools import (
    cancelar_reserva,
    consultar_alergenos,
    crear_reserva,
    revisar_disponibilidad,
)


def tool_revisar_disponibilidad(fecha: str, hora: str, personas: int) -> dict[str, Any]:
    """Consulta la disponibilidad de mesas para una fecha, hora y cantidad de personas.

    Args:
        fecha: Fecha en formato AAAA-MM-DD (ejemplo: 2026-11-05).
        hora: Hora del turno en formato HH:MM (turnos de almuerzo 12:00 a 15:30 o cena 20:00 a 23:30).
        personas: Cantidad de comensales (de 1 a 8 personas).
    """
    res = revisar_disponibilidad(fecha=fecha, hora=hora, personas=personas)
    return res.model_dump()


def tool_crear_reserva(nombre: str, fecha: str, hora: str, personas: int) -> dict[str, Any]:
    """Crea una reserva en el restaurante una vez confirmados los datos con el cliente.

    Args:
        nombre: Nombre completo del titular de la reserva.
        fecha: Fecha de la reserva en formato AAAA-MM-DD.
        hora: Hora de la reserva en formato HH:MM.
        personas: Cantidad de personas (de 1 a 8).
    """
    res = crear_reserva(nombre=nombre, fecha=fecha, hora=hora, personas=personas)
    return res.model_dump()


def tool_cancelar_reserva(id_reserva: str) -> dict[str, Any]:
    """Cancela una reserva existente utilizando su código identificador.

    Args:
        id_reserva: Código único de la reserva (ejemplo: RES-1001).
    """
    res = cancelar_reserva(id_reserva=id_reserva)
    return res.model_dump()


def tool_consultar_alergenos(nombre_plato: str, alergeno: str = "") -> dict[str, Any]:
    """Consulta los alérgenos conocidos de un plato del menú de Trattoria Bella Vista.

    Args:
        nombre_plato: Nombre del plato consultado (ejemplo: Risotto de hongos, Ensalada Caprese).
        alergeno: Alérgeno específico a verificar (ejemplo: gluten, lacteos, nueces). Opcional.
    """
    alerg = alergeno.strip() if alergeno else None
    res = consultar_alergenos(nombre_plato=nombre_plato, alergeno=alerg)
    return res.model_dump()


AGENT_TOOLS = [
    tool_revisar_disponibilidad,
    tool_crear_reserva,
    tool_cancelar_reserva,
    tool_consultar_alergenos,
]
