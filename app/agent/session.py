import uuid
from typing import Dict
from app.agent.core import VoiceReservationAgent


class SessionManager:
    """Administrador en memoria de sesiones conversacionales."""

    def __init__(self) -> None:
        self._sessions: Dict[str, VoiceReservationAgent] = {}

    def get_or_create(self, session_id: str | None = None) -> tuple[str, VoiceReservationAgent]:
        """Obtiene una sesión existente o inicializa una nueva con un identificador UUID."""
        sid = session_id.strip() if session_id and session_id.strip() else str(uuid.uuid4())
        if sid not in self._sessions:
            self._sessions[sid] = VoiceReservationAgent()
        return sid, self._sessions[sid]

    def remove(self, session_id: str) -> bool:
        """Elimina una sesión activa."""
        return self._sessions.pop(session_id, None) is not None

    def clear(self) -> None:
        """Limpia todas las sesiones en memoria."""
        self._sessions.clear()


session_manager = SessionManager()
