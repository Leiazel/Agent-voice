from typing import Any, Optional
from pydantic import BaseModel, Field


class RevisarDisponibilidadInput(BaseModel):
    fecha: str = Field(..., description="Fecha de la reserva en formato AAAA-MM-DD (ej: 2026-10-26)")
    hora: str = Field(..., description="Hora de la reserva en formato HH:MM (ej: 20:30)")
    personas: int = Field(..., description="Cantidad de comensales (1 a 8)")


class DisponibilidadOutput(BaseModel):
    disponible: bool = Field(..., description="Indica si hay mesa disponible para la fecha, hora y personas solicitadas")
    horarios_disponibles: list[str] = Field(default_factory=list, description="Horarios alternativos disponibles si la hora pedida no está libre")
    mensaje: str = Field(..., description="Explicación en lenguaje natural para el usuario")


class CrearReservaInput(BaseModel):
    nombre: str = Field(..., min_length=2, description="Nombre y apellido del titular de la reserva")
    fecha: str = Field(..., description="Fecha de la reserva en formato AAAA-MM-DD")
    hora: str = Field(..., description="Hora de la reserva en formato HH:MM")
    personas: int = Field(..., description="Cantidad de personas (1 a 8)")


class CrearReservaOutput(BaseModel):
    exito: bool = Field(..., description="Indica si la reserva fue creada exitosamente")
    confirmada: bool = Field(default=False, description="Estado de confirmación de la reserva")
    id_reserva: Optional[str] = Field(default=None, description="Identificador único de la reserva (ej: RES-1001)")
    detalles: Optional[dict[str, Any]] = Field(default=None, description="Resumen de los datos de la reserva")
    mensaje: str = Field(..., description="Mensaje en lenguaje natural para comunicar al cliente")


class CancelarReservaInput(BaseModel):
    id_reserva: str = Field(..., min_length=1, description="Identificador de la reserva a cancelar (ej: RES-1001)")


class CancelarReservaOutput(BaseModel):
    exito: bool = Field(..., description="Indica si la reserva fue cancelada exitosamente")
    id_reserva: str = Field(..., description="Identificador de la reserva procesada")
    mensaje: str = Field(..., description="Mensaje en lenguaje natural para comunicar al cliente")


class ConsultarAlergenosInput(BaseModel):
    nombre_plato: str = Field(..., min_length=2, description="Nombre del plato consultado")
    alergeno: Optional[str] = Field(default=None, description="Alérgeno específico a verificar (ej: gluten, lacteos, nueces)")


class ConsultarAlergenosOutput(BaseModel):
    encontrado: bool = Field(..., description="Indica si el plato existe en el menú")
    plato: Optional[str] = Field(default=None, description="Nombre exacto del plato en el menú")
    alergenos_conocidos: list[str] = Field(default_factory=list, description="Lista de alérgenos declarados en el menú para este plato")
    alergeno_consultado: Optional[str] = Field(default=None, description="Alérgeno puntual por el que se preguntó")
    estado: str = Field(..., description="Estado del resultado: 'contiene', 'no_informado', 'plato_inexistente'")
    mensaje: str = Field(..., description="Respuesta clara que respeta el protocolo de seguridad de alérgenos")
