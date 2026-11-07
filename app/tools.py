"""Lecture 03: herramientas del agente.

Los docstrings y las anotaciones de tipos de estas funciones se convierten directamente en las
«descripciones de herramientas» que recibe el modelo. Cambiarlas influye en si usa una herramienta
y en los argumentos con los que la llama.
"""

import json
import random
from functools import cache
from pathlib import Path

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


def make_quiz(lecture: int) -> str:
    """Genera una pregunta de repaso a partir del glosario de una sesión.

    Úsala cuando el usuario solicite una pregunta de repaso o un quiz
    de una Lecture específica. Indica el número de sesión en lecture.
    """
    glossary = load_glossary()

    terms = [
        entry for entry in glossary
        if entry["lecture"] == lecture
    ]

    if not terms:
        return json.dumps(
            {
                "message": f"No hay términos disponibles para Lecture {lecture:02d}."
            },
            ensure_ascii=False,
        )

    selected = random.choice(terms)

    return json.dumps(
        {
            "question": f"¿Qué significa {selected['term']}?",
            "answer": selected["definition"],
        },
        ensure_ascii=False,
    )


def save_learning_log(topic: str, notes: str) -> str:
    """Guarda un registro de aprendizaje en un archivo Markdown.

    Úsala cuando el estudiante solicite explícitamente guardar
    sus apuntes o registrar lo aprendido sobre un tema.
    Esta operación modifica archivos y requiere aprobación humana.
    """
    log_dir = Path(__file__).resolve().parent.parent / "learning_log"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / "learning_log.md"

    with log_path.open("a", encoding="utf-8") as file:
        file.write(f"\n## {topic}\n\n{notes}\n")

    return f"Registro de aprendizaje guardado en {log_path}"
