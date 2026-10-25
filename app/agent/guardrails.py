import re

INJECTION_PATTERNS = [
    r"ignora\s+(todas\s+)?(las\s+|tus\s+|cualquier\s+)?(instrucciones|reglas|directivas|par[aá]metros)(\s+anteriores)?",
    r"olvida\s+(todo\s+)?(lo\s+|tus\s+|las\s+)?(anterior|instrucciones|reglas)",
    r"forget\s+(all\s+)?(previous\s+)?instructions",
    r"disregard\s+(all\s+)?(previous\s+)?instructions",
    r"you\s+are\s+now",
    r"ahora\s+eres\s+(un|una)?",
    r"tu\s+nuevo\s+rol\s+es",
    r"act[uú]a\s+como",
    r"finge\s+(que\s+)?eres",
    r"pretend\s+you\s+are",
    r"modo\s+desarrollador",
    r"developer\s+mode",
    r"jailbreak",
    r"revela\s+(tu|tus)\s+(prompt|instrucciones|sistema|directivas)",
    r"cu[aá]l\s+es\s+tu\s+prompt",
    r"mu[eé]strame\s+tu\s+prompt",
    r"show\s+(your\s+)?system\s+prompt",
    r"system\s*:",
    r"dan\s+mode",
]

OUT_OF_SCOPE_PATTERNS = [
    r"(escribe|hazme|crea|dame)\s+(un\s+|una\s+)?(script|c[oó]digo|programa|funci[oó]n|algoritmo)(\s+en|\s+de)?\s*(python|javascript|java|c\+\+|sql|rust)?",
    r"(qui[eé]n|cu[aá]ndo)\s+(gan[oó]|descubri[oó]|invent[oó]|conquist[oó])",
    r"cu[aá]l\s+es\s+la\s+capital\s+de",
    r"teor[ií]a\s+de\s+la\s+relatividad",
    r"(invertir|comprar)\s+(en\s+)?(cripto|bitcoin|acciones|bolsa)",
    r"(reserva|vuelo|hotel|habitaci[oó]n)\s+(en|para)?\s*(un\s+hotel|un\s+avi[oó]n|aerol[ií]nea)",
    r"(qui[eé]n\s+es\s+el\s+presidente|elecciones\s+presidenciales)",
]


def detect_prompt_injection(text: str) -> bool:
    """Detecta si el mensaje del usuario intenta saltar o alterar las directivas del agente."""
    text_lower = text.lower().strip()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def detect_out_of_scope(text: str) -> bool:
    """Detecta intenciones claramente ajenas a la gestión del restaurante o reservas."""
    text_lower = text.lower().strip()
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def is_unintelligible(text: str) -> bool:
    """Detecta si el texto es ruido ininteligible, teclado aporreado o carente de palabras coherentes."""
    cleaned = text.strip()
    if not cleaned:
        return True

    # Solo caracteres de puntuación o símbolos
    if re.fullmatch(r"^[^\w\s]+$", cleaned):
        return True

    # Repetición exagerada de una misma letra (ej: "aaaaaaa", "zzzzzzzzz")
    if re.search(r"(\w)\1{5,}", cleaned):
        return True

    # Detección de cadenas de consonantes inverosímiles en español (5 o más consonantes seguidas)
    if re.search(r"[b-df-hj-np-tv-z]{5,}", cleaned.lower()):
        return True

    # Palabra alfabética larga sin vocales
    words = cleaned.split()
    for w in words:
        clean_w = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ]", "", w)
        if len(clean_w) > 5 and not re.search(r"[aeiouáéíóúüAEIOUÁÉÍÓÚÜ]", clean_w):
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
