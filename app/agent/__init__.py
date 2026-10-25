"""Módulo principal del agente de voz."""

from app.agent.core import VoiceReservationAgent
from app.agent.guardrails import (
    detect_out_of_scope,
    detect_prompt_injection,
    is_unintelligible,
    sanitize_for_speech,
)
from app.agent.prompts import SYSTEM_PROMPT

__all__ = [
    "VoiceReservationAgent",
    "detect_prompt_injection",
    "detect_out_of_scope",
    "is_unintelligible",
    "sanitize_for_speech",
    "SYSTEM_PROMPT",
]
