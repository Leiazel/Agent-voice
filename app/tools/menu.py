import json
import unicodedata
from pathlib import Path
from app.config import settings
from app.tools.models import ConsultarAlergenosInput, ConsultarAlergenosOutput


def _normalize_text(text: str) -> str:
    """Normaliza texto eliminando acentos, caracteres especiales y guiones bajos."""
    text = text.lower().strip().replace("_", " ")
    norm = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    # Equivalencia fonética italiana/española: 'gn' (lasagna) <-> 'n' (lasaña/lasana)
    return norm.replace("gn", "n")


def cargar_menu(menu_path: Path | None = None) -> list[dict]:
    """Carga los platos desde el archivo JSON del menú."""
    path = menu_path or settings.menu_file_path
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("platos", [])


def buscar_plato_en_menu(nombre_plato: str, platos: list[dict]) -> dict | None:
    """Busca un plato por coincidencia exacta o parcial en el nombre."""
    busqueda = _normalize_text(nombre_plato)
    
    # Coincidencia exacta normalizada
    for plato in platos:
        if _normalize_text(plato["nombre"]) == busqueda:
            return plato
            
    # Coincidencia por subcadena
    for plato in platos:
        nombre_norm = _normalize_text(plato["nombre"])
        if busqueda in nombre_norm or nombre_norm in busqueda:
            return plato
            
    return None


def consultar_alergenos(
    nombre_plato: str,
    alergeno: str | None = None,
    menu_path: Path | None = None,
) -> ConsultarAlergenosOutput:
    """
    Consulta los alérgenos de un plato respetando estrictamente la regla de seguridad:
    si un alérgeno no está declarado explícitamente, no se asume seguro.
    """
    # Validación de entrada vía Pydantic
    params = ConsultarAlergenosInput(nombre_plato=nombre_plato, alergeno=alergeno)
    
    platos = cargar_menu(menu_path)
    plato = buscar_plato_en_menu(params.nombre_plato, platos)
    
    if not plato:
        return ConsultarAlergenosOutput(
            encontrado=False,
            plato=None,
            alergenos_conocidos=[],
            alergeno_consultado=params.alergeno,
            estado="plato_inexistente",
            mensaje=f"El plato '{params.nombre_plato}' no se encuentra en el menú del restaurante.",
        )
        
    alergenos_declarados = plato.get("alergenos", [])
    alergenos_norm = [_normalize_text(a) for a in alergenos_declarados]
    
    # Caso 1: Se consulta un alérgeno específico
    if params.alergeno:
        alergeno_consultado_norm = _normalize_text(params.alergeno)
        if alergeno_consultado_norm in alergenos_norm:
            return ConsultarAlergenosOutput(
                encontrado=True,
                plato=plato["nombre"],
                alergenos_conocidos=alergenos_declarados,
                alergeno_consultado=params.alergeno,
                estado="contiene",
                mensaje=f"Sí, el plato '{plato['nombre']}' contiene {params.alergeno}.",
            )
        else:
            # REGLA DE SEGURIDAD OBLIGATORIA: Nunca afirmar que es seguro si no está declarado
            return ConsultarAlergenosOutput(
                encontrado=True,
                plato=plato["nombre"],
                alergenos_conocidos=alergenos_declarados,
                alergeno_consultado=params.alergeno,
                estado="no_informado",
                mensaje=(
                    f"El menú no declara explícitamente '{params.alergeno}' en el plato '{plato['nombre']}'. "
                    "Por seguridad, no podemos confirmar que sea seguro contra contaminación cruzada; "
                    "por favor confirme con el personal del restaurante."
                ),
            )

    # Caso 2: Consulta general de alérgenos del plato
    if alergenos_declarados:
        lista_alergenos = ", ".join(alergenos_declarados)
        return ConsultarAlergenosOutput(
            encontrado=True,
            plato=plato["nombre"],
            alergenos_conocidos=alergenos_declarados,
            alergeno_consultado=None,
            estado="contiene",
            mensaje=(
                f"El plato '{plato['nombre']}' tiene declarados los siguientes alérgenos: {lista_alergenos}. "
                "Para otros alérgenos no declarados, por favor confirme con el personal del restaurante."
            ),
        )
    else:
        return ConsultarAlergenosOutput(
            encontrado=True,
            plato=plato["nombre"],
            alergenos_conocidos=[],
            alergeno_consultado=None,
            estado="no_informado",
            mensaje=(
                f"El plato '{plato['nombre']}' no tiene alérgenos declarados en el menú. "
                "No garantizamos la ausencia total de trazas; por favor confirme con el personal del restaurante."
            ),
        )

