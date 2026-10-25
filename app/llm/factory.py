from app.config import settings
from app.llm.base import BaseLLM
from app.llm.gemini import GeminiProvider
from app.llm.mock import MockLLM


def get_llm_provider(provider_name: str | None = None) -> BaseLLM:
    """Fábrica de proveedores de LLM según configuración."""
    name = (provider_name or settings.llm_provider).lower().strip()
    if name == "gemini":
        return GeminiProvider()
    elif name == "mock":
        return MockLLM()
    else:
        raise ValueError(f"Proveedor de LLM no soportado o aún no implementado: '{name}'")
