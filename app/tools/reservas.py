from datetime import date, datetime, time
from pathlib import Path
from typing import Optional
from app.tools.db import get_db_connection, init_db
from app.tools.models import (
    CancelarReservaInput,
    CancelarReservaOutput,
    CrearReservaInput,
    CrearReservaOutput,
    DisponibilidadOutput,
    RevisarDisponibilidadInput,
)

MIN_PERSONAS = 1
MAX_PERSONAS = 8
DURACION_RESERVA_MINUTOS = 120

HORARIOS_ALMUERZO = [
    time(12, 0), time(12, 30), time(13, 0), time(13, 30),
    time(14, 0), time(14, 30), time(15, 0)
]

HORARIOS_CENA = [
    time(20, 0), time(20, 30), time(21, 0), time(21, 30),
    time(22, 0), time(22, 30), time(23, 0)
]

TODOS_LOS_HORARIOS = HORARIOS_ALMUERZO + HORARIOS_CENA


def _parsear_fecha_hora(fecha_str: str, hora_str: str) -> tuple[date, time]:
    """Valida y parsea cadenas de fecha y hora ISO."""
    d = date.fromisoformat(fecha_str.strip())
    # Acepta formatos HH:MM o HH:MM:SS
    partes = hora_str.strip().split(":")
    if len(partes) < 2:
        raise ValueError("Formato de hora inválido. Use HH:MM")
    t = time(int(partes[0]), int(partes[1]))
    return d, t


def _minutos_desde_medianoche(t: time) -> int:
    return t.hour * 60 + t.minute


def _hay_solapamiento(t1: time, t2: time) -> bool:
    m1 = _minutos_desde_medianoche(t1)
    m2 = _minutos_desde_medianoche(t2)
    return abs(m1 - m2) < DURACION_RESERVA_MINUTOS


def _es_horario_valido(t: time) -> bool:
    """Verifica si la hora coincide exactamente con los turnos de servicio."""
    return any(t.hour == h.hour and t.minute == h.minute for h in TODOS_LOS_HORARIOS)


def _generar_siguiente_id_reserva(conn) -> str:
    """Genera un ID amigable y secuencial en formato RES-XXXX."""
    cursor = conn.execute(
        "SELECT id FROM reservas ORDER BY rowid DESC LIMIT 1;"
    )
    row = cursor.fetchone()
    if not row or not row["id"].startswith("RES-"):
        return "RES-1001"
    try:
        num = int(row["id"].split("-")[1])
        return f"RES-{num + 1}"
    except (IndexError, ValueError):
        return "RES-1001"


def _buscar_mesa_disponible(
    conn,
    fecha: date,
    hora: time,
    personas: int,
) -> int | None:
    """Busca una mesa libre que se adapte al tamaño del grupo optimizando capacidad."""
    cursor = conn.execute(
        """
        SELECT id, capacidad
        FROM mesas
        WHERE capacidad >= ?
        ORDER BY capacidad ASC, id ASC;
        """,
        (personas,)
    )
    candidatas = cursor.fetchall()
    if not candidatas:
        return None

    # Reservas activas en la misma fecha
    cursor = conn.execute(
        """
        SELECT mesa_id, hora
        FROM reservas
        WHERE fecha = ? AND estado = 'activa';
        """,
        (fecha.isoformat(),)
    )
    reservas_dia = cursor.fetchall()

    for mesa in candidatas:
        mesa_id = mesa["id"]
        mesa_ocupada = False
        for res in reservas_dia:
            if res["mesa_id"] == mesa_id:
                res_hora = time.fromisoformat(res["hora"])
                if _hay_solapamiento(hora, res_hora):
                    mesa_ocupada = True
                    break
        if not mesa_ocupada:
            return mesa_id

    return None


def revisar_disponibilidad(
    fecha: str,
    hora: str,
    personas: int,
    db_path: Path | None = None,
    ahora_ref: datetime | None = None,
) -> DisponibilidadOutput:
    """Revisa si hay mesa disponible para la fecha, hora y personas indicadas."""
    init_db(db_path)
    
    # Validaciones básicas
    if personas < MIN_PERSONAS or personas > MAX_PERSONAS:
        return DisponibilidadOutput(
            disponible=False,
            horarios_disponibles=[],
            mensaje=(
                f"La cantidad de personas ({personas}) está fuera de rango. "
                "Aceptamos reservas de 1 a 8 personas; para grupos mayores, contacte directamente al restaurante."
            ),
        )

    try:
        f_date, h_time = _parsear_fecha_hora(fecha, hora)
    except ValueError:
        return DisponibilidadOutput(
            disponible=False,
            horarios_disponibles=[],
            mensaje="Formato de fecha u hora no válido. Use AAAA-MM-DD para la fecha y HH:MM para la hora.",
        )

    # Verificación de fecha/hora pasada
    ahora = ahora_ref or datetime.now()
    dt_solicitado = datetime.combine(f_date, h_time)
    if dt_solicitado < ahora:
        return DisponibilidadOutput(
            disponible=False,
            horarios_disponibles=[],
            mensaje="La fecha u horario solicitado ya pasó. Por favor seleccione un horario futuro.",
        )

    # Verificación de horario de atención
    if not _es_horario_valido(h_time):
        return DisponibilidadOutput(
            disponible=False,
            horarios_disponibles=[],
            mensaje=(
                "El horario solicitado está fuera de servicio. "
                "Abrimos para almuerzo de 12:00 a 15:30 y para cena de 20:00 a 23:30 (turnos cada 30 min)."
            ),
        )

    # Consulta en base de datos
    with get_db_connection(db_path) as conn:
        mesa_id = _buscar_mesa_disponible(conn, f_date, h_time, personas)
        if mesa_id is not None:
            return DisponibilidadOutput(
                disponible=True,
                horarios_disponibles=[h_time.strftime("%H:%M")],
                mensaje=f"Tenemos disponibilidad para {personas} personas el {fecha} a las {hora}.",
            )

        # Buscar horarios alternativos disponibles en el mismo día
        alternativas: list[str] = []
        for turno in TODOS_LOS_HORARIOS:
            if datetime.combine(f_date, turno) >= ahora:
                if _buscar_mesa_disponible(conn, f_date, turno, personas) is not None:
                    alternativas.append(turno.strftime("%H:%M"))

        if alternativas:
            alt_str = ", ".join(alternativas[:5])
            return DisponibilidadOutput(
                disponible=False,
                horarios_disponibles=alternativas,
                mensaje=f"No hay mesas libres a las {hora}. Los horarios alternativos disponibles son: {alt_str}.",
            )
        else:
            return DisponibilidadOutput(
                disponible=False,
                horarios_disponibles=[],
                mensaje=f"No disponemos de mesas para {personas} personas en ninguna franja del día {fecha}.",
            )


def crear_reserva(
    nombre: str,
    fecha: str,
    hora: str,
    personas: int,
    db_path: Path | None = None,
    ahora_ref: datetime | None = None,
) -> CrearReservaOutput:
    """Crea una reserva asegurando validación de disponibilidad y unicidad."""
    init_db(db_path)
    
    nombre_limpio = nombre.strip()
    if len(nombre_limpio) < 2:
        return CrearReservaOutput(
            exito=False,
            confirmada=False,
            mensaje="El nombre del titular debe tener al menos 2 caracteres.",
        )

    # Reutiliza validación de disponibilidad completa
    disp = revisar_disponibilidad(fecha, hora, personas, db_path=db_path, ahora_ref=ahora_ref)
    if not disp.disponible:
        return CrearReservaOutput(
            exito=False,
            confirmada=False,
            mensaje=f"No se pudo crear la reserva: {disp.mensaje}",
        )

    f_date, h_time = _parsear_fecha_hora(fecha, hora)

    with get_db_connection(db_path) as conn:
        # Chequeo de duplicado (mismo titular en la misma fecha y horario solapado)
        cursor = conn.execute(
            """
            SELECT id, hora FROM reservas
            WHERE LOWER(nombre) = LOWER(?) AND fecha = ? AND estado = 'activa';
            """,
            (nombre_limpio, f_date.isoformat())
        )
        for row in cursor.fetchall():
            res_hora = time.fromisoformat(row["hora"])
            if _hay_solapamiento(h_time, res_hora):
                return CrearReservaOutput(
                    exito=False,
                    confirmada=False,
                    mensaje=(
                        f"Ya existe una reserva activa para '{nombre_limpio}' el {fecha} "
                        f"a las {res_hora.strftime('%H:%M')} (código {row['id']})."
                    ),
                )

        mesa_id = _buscar_mesa_disponible(conn, f_date, h_time, personas)
        if mesa_id is None:
            return CrearReservaOutput(
                exito=False,
                confirmada=False,
                mensaje="La mesa ya no se encuentra disponible. Por favor intente con otro horario.",
            )

        id_reserva = _generar_siguiente_id_reserva(conn)
        conn.execute(
            """
            INSERT INTO reservas (id, nombre, fecha, hora, personas, mesa_id, estado)
            VALUES (?, ?, ?, ?, ?, ?, 'activa');
            """,
            (
                id_reserva,
                nombre_limpio,
                f_date.isoformat(),
                h_time.strftime("%H:%M"),
                personas,
                mesa_id,
            )
        )

        detalles = {
            "id_reserva": id_reserva,
            "nombre": nombre_limpio,
            "fecha": f_date.isoformat(),
            "hora": h_time.strftime("%H:%M"),
            "personas": personas,
            "mesa_id": mesa_id,
        }

        return CrearReservaOutput(
            exito=True,
            confirmada=True,
            id_reserva=id_reserva,
            detalles=detalles,
            mensaje=(
                f"Reserva confirmada con éxito. Código: {id_reserva} a nombre de {nombre_limpio} "
                f"para {personas} personas el {fecha} a las {h_time.strftime('%H:%M')}."
            ),
        )


def cancelar_reserva(
    id_reserva: str,
    db_path: Path | None = None,
) -> CancelarReservaOutput:
    """Cancela una reserva existente por su código identificador."""
    init_db(db_path)
    
    codigo = id_reserva.strip().upper()
    if not codigo:
        return CancelarReservaOutput(
            exito=False,
            id_reserva=id_reserva,
            mensaje="Debe proporcionar un código de reserva válido.",
        )

    with get_db_connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT id, nombre, fecha, hora, estado FROM reservas WHERE id = ?;",
            (codigo,)
        )
        reserva = cursor.fetchone()

        if not reserva:
            return CancelarReservaOutput(
                exito=False,
                id_reserva=codigo,
                mensaje=f"No se encontró ninguna reserva registrada con el código '{codigo}'.",
            )

        if reserva["estado"] == "cancelada":
            return CancelarReservaOutput(
                exito=False,
                id_reserva=codigo,
                mensaje=f"La reserva '{codigo}' ya se encontraba cancelada.",
            )

        conn.execute(
            "UPDATE reservas SET estado = 'cancelada' WHERE id = ?;",
            (codigo,)
        )

        return CancelarReservaOutput(
            exito=True,
            id_reserva=codigo,
            mensaje=f"La reserva '{codigo}' a nombre de {reserva['nombre']} ha sido cancelada exitosamente.",
        )
