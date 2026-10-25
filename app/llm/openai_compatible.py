import json
from typing import Any, Callable
import httpx

from app.config import settings
from app.llm.base import BaseLLM, LLMResponse, ToolExecution


class OpenAICompatibleProvider(BaseLLM):
    """
    Proveedor para APIs compatibles con OpenAI (Groq, OpenRouter, etc.).
    Permite correr modelos abiertos de alta velocidad en la nube de forma gratuita (ej. Llama 3.3 70B en Groq).
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model

    def send_message(
        self,
        message: str,
        conversation_history: list[dict[str, str]],
        system_instruction: str,
        tools: list[Callable] | None = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY (o clave de Groq/OpenRouter) no configurada. Configure OPENAI_API_KEY en .env"
            )

        messages = [{"role": "system", "content": system_instruction}]
        for turn in conversation_history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": message})

        tool_defs = []
        tool_map: dict[str, Callable] = {}
        if tools:
            for tool_fn in tools:
                tool_map[tool_fn.__name__] = tool_fn
                tool_defs.append(self._convert_tool_schema(tool_fn))

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        tool_executions: list[ToolExecution] = []
        current_messages = list(messages)

        # Loop de ejecución de function calling (hasta 5 iteraciones)
        for _ in range(5):
            payload: dict[str, Any] = {
                "model": self.model,
                "messages": current_messages,
                "temperature": 0.2,
            }
            if tool_defs:
                payload["tools"] = tool_defs
                payload["tool_choice"] = "auto"

            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            choice = data["choices"][0]
            msg = choice["message"]

            if not msg.get("tool_calls"):
                return LLMResponse(
                    text=msg.get("content") or "",
                    tool_executions=tool_executions,
                )

            current_messages.append(msg)

            for tc in msg["tool_calls"]:
                fn_name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"]["arguments"])
                except Exception:
                    args = {}

                fn = tool_map.get(fn_name)
                output = fn(**args) if fn else {"error": f"Herramienta {fn_name} desconocida"}
                tool_executions.append(
                    ToolExecution(name=fn_name, args=args, output=output)
                )

                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": fn_name,
                    "content": json.dumps(output, ensure_ascii=False),
                })

        return LLMResponse(
            text="Se excedió el límite de iteraciones de herramientas.",
            tool_executions=tool_executions,
        )

    @staticmethod
    def _convert_tool_schema(fn: Callable) -> dict[str, Any]:
        """Convierte una función Python anotada a formato JSON Schema para function calling."""
        import inspect
        sig = inspect.signature(fn)
        props: dict[str, Any] = {}
        required: list[str] = []

        for name, param in sig.parameters.items():
            py_type = param.annotation
            type_str = "string"
            if py_type is int:
                type_str = "integer"
            elif py_type is bool:
                type_str = "boolean"

            props[name] = {"type": type_str, "description": f"Parámetro {name}"}
            if param.default is inspect.Parameter.empty:
                required.append(name)

        return {
            "type": "function",
            "function": {
                "name": fn.__name__,
                "description": fn.__doc__ or fn.__name__,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": required,
                },
            },
        }
