import pytest
from app.config import settings
from app.llm.liquid import LiquidDecisionClient, LiquidProvider
from app.llm.factory import get_llm_provider


def test_liquid_config_loaded() -> None:
    assert settings.liquid_api_key.startswith("liquid_")
    assert settings.liquid_base_url == "https://api.liquid.ai"
    assert settings.liquid_model == "d1.1"


def test_liquid_provider_factory() -> None:
    provider = get_llm_provider("liquid")
    assert isinstance(provider, LiquidProvider)
    assert provider.client.api_key == settings.liquid_api_key


@pytest.mark.skipif(
    not settings.liquid_api_key,
    reason="Requiere LIQUID_API_KEY configurada para probar llamada en vivo a Liquid AI",
)
def test_liquid_live_decision_call() -> None:
    client = LiquidDecisionClient()
    result = client.evaluate(
        state="Cliente: Hola, me gustaría saber si tienen mesas libres para dos personas hoy a las 21:00",
        questions={
            "is_out_of_scope": {
                "type": "noul",
                "instructions": "Is this inquiry unrelated to restaurant operations or reservations?",
            },
            "intent": {
                "type": "choice",
                "instructions": "¿Cuál es la intención del cliente?",
                "criteria": {
                    "reservation": "El cliente desea reservar o consultar disponibilidad",
                    "other": "Cualquier otra consulta",
                },
            },
        },
    )
    assert result.get("model") in ("d1", "d1.1", "d1-ultra")
    answers = result.get("answers", {})
    assert "is_out_of_scope" in answers
    assert answers["intent"]["choice"] == "reservation"

