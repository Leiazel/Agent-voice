from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title="Restaurant Voice Agent",
    description="Agente conversacional de voz para reservas gastronómicas",
    version="0.1.0",
)


@app.get("/health", tags=["Salud"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "env": settings.app_env,
    }
