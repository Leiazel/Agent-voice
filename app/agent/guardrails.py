import re

INJECTION_PATTERNS = [
    r"ignora\s+(las\s+|tus\s+|cualquier\s+)?(instrucciones|reglas|directivas)\s+anteriores",
    r"olvida\s+(todo\s+)?(lo\s+|tus\s+|las\s+)?(anterior|instrucciones|reglas)",
    r"forget\s+(all\s+)?(previous\s+)?instructions",
    r"you\s+are\s+now",
    r"ahora\s+eres\s+(un|una)?",
    r"act[uú]a\s+como",
    r"modo\s+desarrollador",
    r"developer\s+mode",
    r"jailbreak",
    r"revela\s+(tu|tus)\s+(prompt|instrucciones|sistema)",
    r"show\s+(your\s+)?system\s+prompt",
    r"system\s*:",
    r"dan\s+mode",
]


def detect_prompt_injection(text: str) -> bool:
    """Detecta si el mensaje del usuario intenta saltar o alterar las directivas del agente."""
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def sanitize_for_speech(text: str) -> str:
    """
    Limpia la salida eliminando marcas de formato markdown (asteriscos, numerales,
    guiones de listas) para asegurar una locución fluida y natural en sistemas TTS.
    """
    if not text:
        return ""

    # Quitar negritas y cursivas (**texto**, *texto*)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    
    # Quitar encabezados (# Encabezado)
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
    
    # Quitar viñetas de lista (- item, * item, 1. item)
    cleaned = re.sub(r"^\s*[-*•]\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*\d+\.\s*", "", cleaned, flags=re.MULTILINE)
    
    # Quitar backticks de código (`codigo`)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    
    # Reducir saltos de línea repetidos a un solo espacio o punto y aparte
    cleaned = re.sub(r"\n+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned
