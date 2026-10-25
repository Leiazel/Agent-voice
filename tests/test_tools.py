from datetime import datetime
from pathlib import Path
import pytest

from app.tools import (
    cancelar_reserva,
    consultar_alergenos,
    crear_reserva,
    revisar_disponibilidad,
)
from app.tools.db import init_db

REF_NOW = datetime(2026, 11, 1, 10, 0)
FECHA_FUTURA = "2026-11-05"
FECHA_PASADA = "2026-10-01"


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Fixture que crea una base de datos SQLite limpia y temporal para cada test."""
    db_file = tmp_path / "test_reservas.db"
    init_db(db_file)
    return db_file


# ==============================================================================
# TESTS: revisar_disponibilidad
# ==============================================================================

def test_disponibilidad_caso_feliz(temp_db: Path) -> None:
    res = revisar_disponibilidad(
        fecha=FECHA_FUTURA,
        hora="20:30",
        personas=2,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res.disponible is True
    assert "20:30" in res.horarios_disponibles
    assert "disponibilidad" in res.mensaje.lower()


def test_disponibilidad_fecha_pasada(temp_db: Path) -> None:
    res = revisar_disponibilidad(
        fecha=FECHA_PASADA,
        hora="13:00",
        personas=4,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res.disponible is False
    assert "ya pasó" in res.mensaje.lower()


def test_disponibilidad_hoy_hora_pasada(temp_db: Path) -> None:
    # Si la referencia es 10:00 y se pide para hoy a las 09:00
    res = revisar_disponibilidad(
        fecha="2026-11-01",
        hora="09:00",
        personas=2,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res.disponible is False
    assert "ya pasó" in res.mensaje.lower()


def test_disponibilidad_fuera_de_horario(temp_db: Path) -> None:
    # 17:00 está entre el turno de almuerzo (cierra 15:30) y cena (abre 20:00)
    res = revisar_disponibilidad(
        fecha=FECHA_FUTURA,
        hora="17:00",
        personas=2,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res.disponible is False
    assert "fuera de servicio" in res.mensaje.lower()


def test_disponibilidad_personas_fuera_de_rango(temp_db: Path) -> None:
    # Menos de 1 persona
    res_cero = revisar_disponibilidad(
        fecha=FECHA_FUTURA,
        hora="20:00",
        personas=0,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res_cero.disponible is False
    assert "fuera de rango" in res_cero.mensaje.lower()

    # Más de 8 personas
    res_muchos = revisar_disponibilidad(
        fecha=FECHA_FUTURA,
        hora="20:00",
        personas=12,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res_muchos.disponible is False
    assert "contacte" in res_muchos.mensaje.lower()


def test_disponibilidad_formato_invalido(temp_db: Path) -> None:
    res = revisar_disponibilidad(
        fecha="fecha-erronea",
        hora="no-es-hora",
        personas=2,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res.disponible is False
    assert "no válido" in res.mensaje.lower()


def test_disponibilidad_mesas_agotadas_ofrece_alternativas(temp_db: Path) -> None:
    # El restaurante tiene:
    # Mesas cap 2: 2 mesas (id 1, 2)
    # Mesas cap 4: 3 mesas (id 3, 4, 5)
    # Mesas cap 6: 1 mesa (id 6)
    # Mesas cap 8: 1 mesa (id 7)
    # Total mesas que soportan 8 personas: solo mesa 7
    # Si reservamos la mesa 7 a las 20:00, para 8 personas ya no habrá mesa a las 20:00
    crear = crear_reserva(
        nombre="Carlos Gomez",
        fecha=FECHA_FUTURA,
        hora="20:00",
        personas=8,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert crear.exito is True

    # Consultamos nuevamente para 8 personas a las 20:00
    res = revisar_disponibilidad(
        fecha=FECHA_FUTURA,
        hora="20:00",
        personas=8,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res.disponible is False
    assert len(res.horarios_disponibles) > 0
    # Como la reserva dura 2 horas (120 min), 20:00, 20:30, 21:00, 21:30 están ocupadas.
    # Pero 22:00 debería estar disponible como alternativa
    assert "22:00" in res.horarios_disponibles


# ==============================================================================
# TESTS: crear_reserva
# ==============================================================================

def test_crear_reserva_caso_feliz(temp_db: Path) -> None:
    res = crear_reserva(
        nombre="Laura Pausini",
        fecha=FECHA_FUTURA,
        hora="21:00",
        personas=3,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res.exito is True
    assert res.confirmada is True
    assert res.id_reserva == "RES-1001"
    assert res.detalles is not None
    assert res.detalles["nombre"] == "Laura Pausini"
    assert res.detalles["personas"] == 3


def test_crear_reserva_secuencial_ids(temp_db: Path) -> None:
    res1 = crear_reserva(
        nombre="Cliente Uno",
        fecha=FECHA_FUTURA,
        hora="12:00",
        personas=2,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    res2 = crear_reserva(
        nombre="Cliente Dos",
        fecha=FECHA_FUTURA,
        hora="12:00",
        personas=2,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res1.id_reserva == "RES-1001"
    assert res2.id_reserva == "RES-1002"


def test_crear_reserva_nombre_invalido(temp_db: Path) -> None:
    res = crear_reserva(
        nombre=" ",
        fecha=FECHA_FUTURA,
        hora="21:00",
        personas=2,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res.exito is False
    assert "al menos 2 caracteres" in res.mensaje.lower()


def test_crear_reserva_duplicado(temp_db: Path) -> None:
    # Primera reserva
    res1 = crear_reserva(
        nombre="Martin Palermo",
        fecha=FECHA_FUTURA,
        hora="13:00",
        personas=4,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res1.exito is True

    # Intento de duplicado para el mismo titular en el mismo turno
    res2 = crear_reserva(
        nombre="martin palermo",
        fecha=FECHA_FUTURA,
        hora="13:30",  # Solapado (< 120 min)
        personas=4,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res2.exito is False
    assert "ya existe una reserva activa" in res2.mensaje.lower()


def test_crear_reserva_fecha_pasada(temp_db: Path) -> None:
    res = crear_reserva(
        nombre="Juan Perez",
        fecha=FECHA_PASADA,
        hora="21:00",
        personas=2,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert res.exito is False
    assert "ya pasó" in res.mensaje.lower()


# ==============================================================================
# TESTS: cancelar_reserva
# ==============================================================================

def test_cancelar_reserva_caso_feliz_y_liberacion(temp_db: Path) -> None:
    # Creamos la única mesa para 8 personas
    crear = crear_reserva(
        nombre="Valeria Lynch",
        fecha=FECHA_FUTURA,
        hora="20:00",
        personas=8,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert crear.exito is True
    id_reserva = crear.id_reserva
    assert id_reserva is not None

    # Cancelamos la reserva
    cancel = cancelar_reserva(id_reserva, db_path=temp_db)
    assert cancel.exito is True
    assert "cancelada exitosamente" in cancel.mensaje.lower()

    # Verificamos que la mesa quedó libre nuevamente para las 20:00
    disp = revisar_disponibilidad(
        fecha=FECHA_FUTURA,
        hora="20:00",
        personas=8,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert disp.disponible is True


def test_cancelar_reserva_id_inexistente(temp_db: Path) -> None:
    res = cancelar_reserva("RES-9999", db_path=temp_db)
    assert res.exito is False
    assert "no se encontró ninguna reserva" in res.mensaje.lower()


def test_cancelar_reserva_ya_cancelada(temp_db: Path) -> None:
    crear = crear_reserva(
        nombre="Anibal Troilo",
        fecha=FECHA_FUTURA,
        hora="21:00",
        personas=2,
        db_path=temp_db,
        ahora_ref=REF_NOW,
    )
    assert crear.id_reserva is not None
    cancelar_reserva(crear.id_reserva, db_path=temp_db)

    # Segundo intento de cancelación sobre la misma
    segunda_cancel = cancelar_reserva(crear.id_reserva, db_path=temp_db)
    assert segunda_cancel.exito is False
    assert "ya se encontraba cancelada" in segunda_cancel.mensaje.lower()


# ==============================================================================
# TESTS: consultar_alergenos (Regla de seguridad estricta)
# ==============================================================================

def test_consultar_alergenos_plato_existente_declarado() -> None:
    # Risotto de hongos declara 'lacteos'
    res = consultar_alergenos("Risotto de hongos", alergeno="lacteos")
    assert res.encontrado is True
    assert res.estado == "contiene"
    assert "contiene lacteos" in res.mensaje.lower()


def test_consultar_alergenos_plato_inexistente() -> None:
    res = consultar_alergenos("Tacos al pastor")
    assert res.encontrado is False
    assert res.estado == "plato_inexistente"
    assert "no se encuentra en el menú" in res.mensaje.lower()


def test_consultar_alergenos_seguridad_no_informado() -> None:
    # La Ensalada Caprese solo tiene declarado 'lacteos'.
    # Si el usuario pregunta por 'frutos secos' o 'gluten',
    # el agente NO debe decir "no tiene gluten / es seguro".
    # Debe responder 'no_informado' y remitir al personal.
    res = consultar_alergenos("Ensalada Caprese", alergeno="gluten")
    assert res.encontrado is True
    assert res.estado == "no_informado"
    assert "no podemos confirmar que sea seguro" in res.mensaje.lower()
    assert "personal del restaurante" in res.mensaje.lower()


def test_consultar_alergenos_plato_sin_declaracion_previa() -> None:
    # Sopa Minestrone tiene alergenos=[]
    res = consultar_alergenos("Sopa Minestrone")
    assert res.encontrado is True
    assert res.estado == "no_informado"
    assert "no garantizamos la ausencia total" in res.mensaje.lower()
    assert "personal del restaurante" in res.mensaje.lower()


def test_consultar_alergenos_general_con_alergenos() -> None:
    # Ravioles de ricota y nuez declara: gluten, lacteos, huevo, frutos_secos
    res = consultar_alergenos("Ravioles de ricota y nuez")
    assert res.encontrado is True
    assert res.estado == "contiene"
    assert "frutos_secos" in res.alergenos_conocidos
    assert "gluten" in res.alergenos_conocidos


def test_consultar_alergenos_insensible_mayusculas_tildes() -> None:
    # Probamos con tildes y mayúsculas ("SALMÓN A LA PLANCHA")
    res = consultar_alergenos("salmón", alergeno="pescado")
    assert res.encontrado is True
    assert res.estado == "contiene"

