from app.config import settings
from app.llm.base import BaseLLM
from app.llm.gemini import GeminiProvider
from app.llm.liquid import LiquidProvider
from app.llm.mock import MockLLM
from app.llm.openai_compatible import OpenAICompatibleProvider
from app.logging_config import audit_logger


def get_llm_provider(provider_name: str | None = None) -> BaseLLM:
    """Fábrica de proveedores de LLM según configuración con fallback inteligente entre Gemini y Groq/OpenAI."""
    name = (provider_name or settings.llm_provider).lower().strip()

    if name == "gemini":
        if settings.gemini_api_key.strip():
            return GeminiProvider()
        elif settings.openai_api_key.strip():
            audit_logger.warning(
                "GEMINI_API_KEY no configurada. Usando proveedor Groq/OpenAI disponible."
            )
            return OpenAICompatibleProvider()
        return GeminiProvider()

    elif name in ("openai", "groq", "openrouter"):
        if settings.openai_api_key.strip():
            return OpenAICompatibleProvider()
        elif settings.gemini_api_key.strip():
            audit_logger.warning(
                "OPENAI_API_KEY no configurada. Usando proveedor Gemini disponible."
            )
            return GeminiProvider()
        return OpenAICompatibleProvider()

    elif name == "mock":
        return MockLLM()

    elif name == "liquid":
        return LiquidProvider()

    elif name in ("auto", "default"):
        if settings.gemini_api_key.strip():
            return GeminiProvider()
        elif settings.openai_api_key.strip():
            return OpenAICompatibleProvider()
        return MockLLM()

    else:
        raise ValueError(f"Proveedor de LLM no soportado o aún no implementado: '{name}'")

