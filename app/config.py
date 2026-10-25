from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Entorno y servidor
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Persistencia
    database_path: Path = Field(default=Path("data/reservas.db"), alias="DATABASE_PATH")
    menu_file_path: Path = Field(default=Path("data/menu.json"), alias="MENU_FILE_PATH")

    # Proveedores LLM
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:7b", alias="OLLAMA_MODEL")

    # Pipeline de voz
    vad_provider: str = Field(default="silero", alias="VAD_PROVIDER")
    stt_provider: str = Field(default="faster-whisper", alias="STT_PROVIDER")
    stt_model: str = Field(default="base", alias="STT_MODEL")
    tts_provider: str = Field(default="piper", alias="TTS_PROVIDER")
    tts_model: str = Field(default="es_ES-davefx-medium", alias="TTS_MODEL")


settings = Settings()
