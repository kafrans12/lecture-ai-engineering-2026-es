"""Lecture 03: herramientas del agente.

Los docstrings y las anotaciones de tipos de estas funciones se convierten directamente en las
«descripciones de herramientas» que recibe el modelo. Cambiarlas influye en si usa una herramienta
y en los argumentos con los que la llama.
"""

import json
from functools import cache
from pathlib import Path

from app.config import api_error_message

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """Busca un término en el glosario del curso y devuelve su definición y la sesión en que se trata.

    Úsala antes de responder sobre términos de ingeniería de IA o expresiones específicas de
    este curso (AIE2026). Incluye en query un único término para consultar (por ejemplo, "LoRA").
    """
    q = _normalize(query)
    if not q:
        return "La consulta está vacía. Indica un término que quieras buscar."
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # Excluye nombres cortos para evitar que alias como «r» coincidan con cualquier consulta
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"No se ha encontrado «{query}» en el glosario."
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """Devuelve los puntos clave de la sesión indicada (entero a partir de 1).

    Úsala para preguntas sobre el contenido de las sesiones o su relación,
    como «¿Qué se aprende en Lecture 03?».
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"Todavía no hay puntos clave de Lecture {lecture:02d}. Sesiones disponibles: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


def search_materials(query: str) -> str:
    """Busca en los materiales principales de Lecture 01–03 y devuelve el texto, el título y el número de las páginas relacionadas.

    Indica en query el contenido que quieres consultar.
    """
    from google.genai.errors import APIError
    import sqlite3
    from app.retrieval import search

    try:
        return json.dumps(
            {"results": search(query, expand_neighbors=True)},
            ensure_ascii=False
        )
    except (ValueError, FileNotFoundError, sqlite3.Error) as e:
        return json.dumps({"error": str(e), "results": []}, ensure_ascii=False)
    except APIError as e:
        return json.dumps({"error": api_error_message(e.code), "results": []}, ensure_ascii=False)


def browse_tree(node_id: str | None = None) -> str:
    """Devuelve el índice de contenidos y la primera frase de las páginas. Si indicas un ID de página, devuelve el texto completo.

    Omite node_id al empezar. Después recorre el índice de contenidos indicando los ID devueltos.
    """
    from app.retrieval import browse_tree as browse

    try:
        return json.dumps(browse(node_id), ensure_ascii=False)
    except (ValueError, OSError) as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def search_graph(query: str) -> str:
    """Busca en los materiales y recorre páginas adyacentes y términos comunes para devolver el texto y los datos de cita de las páginas relacionadas.

    Indica en query el contenido que quieres consultar.
    """
    import sqlite3
    from google.genai.errors import APIError
    from app.retrieval import search_graph as search

    try:
        return json.dumps(search(query), ensure_ascii=False)
    except (ValueError, OSError, sqlite3.Error) as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except APIError as e:
        return json.dumps({"error": api_error_message(e.code)}, ensure_ascii=False)
