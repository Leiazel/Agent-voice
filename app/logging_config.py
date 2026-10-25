import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CONVERSATIONS_LOG_FILE = LOGS_DIR / "conversations.jsonl"


class StructuredJsonFormatter(logging.Formatter):
    """Formateador JSON estructurado para auditoría y observabilidad."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Atributos adicionales inyectados en el logging extra
        for key in ("session_id", "user_message", "agent_response", "tools_used", "duration_ms"):
            if hasattr(record, key):
                log_obj[key] = getattr(record, key)

        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configura el sistema de logging para consola y archivo JSONL estructurado."""
    root_logger = logging.getLogger("voice_agent")
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.handlers.clear()

    # Handler de consola legible
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Handler de archivo para conversaciones estructuradas (.jsonl)
    file_handler = logging.FileHandler(CONVERSATIONS_LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(file_handler)

    return root_logger


audit_logger = setup_logging()
