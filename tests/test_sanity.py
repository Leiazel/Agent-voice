from app.config import Settings
from app.main import app


def test_settings_load_defaults() -> None:
    settings = Settings()
    assert settings.app_env in {"development", "testing", "production"}
    assert settings.llm_provider in {"gemini", "ollama", "groq", "openai", "openrouter", "mock", "liquid"}


def test_fastapi_app_initialization() -> None:
    assert app.title == "Restaurant Voice Agent"
