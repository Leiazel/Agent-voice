from abc import ABC, abstractmethod
from typing import Any, Callable
from pydantic import BaseModel, Field


class ToolExecution(BaseModel):
    """Registro de ejecución de una herramienta para observabilidad y métricas."""
    name: str
    args: dict[str, Any]
    output: Any


class LLMResponse(BaseModel):
    """Respuesta unificada de un proveedor de LLM."""
    text: str
    tool_executions: list[ToolExecution] = Field(default_factory=list)


class BaseLLM(ABC):
    """Interfaz abstracta común para todos los proveedores de LLM (Gemini, Ollama, etc.)."""

    @abstractmethod
    def send_message(
        self,
        message: str,
        conversation_history: list[dict[str, str]],
        system_instruction: str,
        tools: list[Callable] | None = None,
    ) -> LLMResponse:
        """
        Envía un mensaje al LLM, permitiendo ejecución de herramientas y preservando el historial.
        
        Args:
            message: Mensaje del usuario.
            conversation_history: Lista de mensajes anteriores [{'role': 'user'|'model', 'content': str}].
            system_instruction: Prompt de sistema y directivas del agente.
            tools: Lista de funciones Python que el modelo puede invocar vía function calling.
        """
        pass
