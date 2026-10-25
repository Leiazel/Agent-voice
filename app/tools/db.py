import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from app.config import settings

DEFAULT_TABLES = [
    (1, 2, "salon_principal"),
    (2, 2, "salon_principal"),
    (3, 4, "salon_principal"),
    (4, 4, "salon_principal"),
    (5, 4, "terraza"),
    (6, 6, "salon_principal"),
    (7, 8, "salon_principal"),
]


@contextmanager
def get_db_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Provee una conexión contextual a la base SQLite con row_factory activado."""
    target_path = db_path or settings.database_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | None = None) -> None:
    """Inicializa el esquema de SQLite y carga las mesas semilla si no existen."""
    with get_db_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS mesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero INTEGER NOT NULL UNIQUE,
                capacidad INTEGER NOT NULL,
                ubicacion TEXT NOT NULL DEFAULT 'salon_principal'
            );

            CREATE TABLE IF NOT EXISTS reservas (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                personas INTEGER NOT NULL,
                mesa_id INTEGER NOT NULL REFERENCES mesas(id),
                estado TEXT NOT NULL DEFAULT 'activa',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_reservas_fecha_hora ON reservas(fecha, hora, estado);
            CREATE INDEX IF NOT EXISTS idx_reservas_nombre ON reservas(nombre, estado);
        """)

        # Insertar mesas iniciales si la tabla está vacía
        cursor = conn.execute("SELECT COUNT(*) AS count FROM mesas;")
        if cursor.fetchone()["count"] == 0:
            conn.executemany(
                "INSERT INTO mesas (numero, capacidad, ubicacion) VALUES (?, ?, ?);",
                DEFAULT_TABLES
            )

