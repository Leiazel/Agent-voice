import functools
from typing import Any, Callable
from google import genai
from google.genai import types

from app.config import settings
from app.llm.base import BaseLLM, LLMResponse, ToolExecution


class GeminiProvider(BaseLLM):
    """Proveedor LLM para Google Gemini utilizando el SDK oficial google-genai."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model

    def send_message(
        self,
        message: str,
        conversation_history: list[dict[str, str]],
        system_instruction: str,
        tools: list[Callable] | None = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY no configurada. Configure GEMINI_API_KEY en el archivo .env"
            )

        client = genai.Client(api_key=self.api_key)
        tool_executions: list[ToolExecution] = []

        # Envolver herramientas para registrar llamadas y argumentos
        wrapped_tools = []
        if tools:
            for tool_fn in tools:
                wrapped_tools.append(self._wrap_tool(tool_fn, tool_executions))

        # Construir historial en formato types.Content
        history_contents: list[types.Content] = []
        for turn in conversation_history:
            role = turn.get("role", "user")
            # En el SDK genai los roles esperados son 'user' o 'model'
            sdk_role = "model" if role in ("assistant", "model") else "user"
            content = turn.get("content", "")
            if content:
                history_contents.append(
                    types.Content(
                        role=sdk_role,
                        parts=[types.Part.from_text(text=content)],
                    )
                )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=wrapped_tools if wrapped_tools else None,
        )

        chat = client.chats.create(
            model=self.model,
            config=config,
            history=history_contents,
        )

        response = chat.send_message(message)
        text_output = response.text or ""

        return LLMResponse(
            text=text_output,
            tool_executions=tool_executions,
        )

    @staticmethod
    def _wrap_tool(tool_fn: Callable, tracking_list: list[ToolExecution]) -> Callable:
        """Envuelve una función de herramienta para capturar sus invocaciones."""
        @functools.wraps(tool_fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = tool_fn(*args, **kwargs)
            tracking_list.append(
                ToolExecution(
                    name=tool_fn.__name__,
                    args=kwargs,
                    output=result,
                )
            )
            return result

        return wrapper
