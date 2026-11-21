"""Configuración compartida por todo el curso.

La clave API y el nombre del modelo se leen de variables de entorno, sin escribirlos en el código.
"""

import os
from pathlib import Path

# Modelo predeterminado. Se cambia mediante la variable de entorno AIE_MODEL.
#   Ejemplo: export AIE_MODEL=gemini-3.5-flash
DEFAULT_MODEL = "gemini-3.5-flash-lite"
MODEL = os.getenv("AIE_MODEL", DEFAULT_MODEL)


# Lecture 05: búsqueda con un fragmento por página. El índice se crea con scripts/build_rag_index.py.
ROOT = Path(__file__).resolve().parent.parent
RAG_SOURCE = ROOT / "data/rag_data/lectures.json"
RAG_TREE = ROOT / "data/rag_data/tree.json"
RAG_GRAPH = ROOT / "data/rag_data/graph.json"
RAG_DB = Path(os.getenv("AIE_RAG_DB", str(ROOT / "data/rag_data/index.sqlite3")))
RAG_DOCUMENT_IDS = ("lec01-main", "lec02-main", "lec03-main")
RAG_TOP_K = 5
GRAPH_START_K = 3
GRAPH_HOPS = 2
GRAPH_MAX_RESULTS = 10
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768
# Reserva margen para la indicación de la tarea y otros datos dentro del límite de 2.048 tokens. Si se supera, se detiene sin truncar.
EMBEDDING_MAX_TOKENS = 2000


def api_error_message(status: int, detail: str = "") -> str:
    """Convierte un código de estado HTTP en una explicación en español para el alumnado (compartida por ask.py y agent.py)."""
    if status == 429:
        return "Se ha alcanzado el límite de uso. Espera aproximadamente 1 minuto y vuelve a intentarlo."
    if status == 503:
        return "El modelo está saturado (503). Espera un poco y vuelve a intentarlo."
    if status in (400, 401, 403, 404):
        return f"Hay un problema con la clave API o el nombre del modelo ({status}): {detail}"
    return f"Error de API ({status}): {detail}"


def get_api_key() -> str:
    """Devuelve la variable de entorno GEMINI_API_KEY. Si falta, muestra las instrucciones y termina."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise SystemExit(
            "No se ha encontrado la variable de entorno GEMINI_API_KEY.\n"
            "1. Registra GEMINI_API_KEY en Settings → Codespaces → Secrets de GitHub y\n"
            "   selecciona tu propio fork como repositorio autorizado.\n"
            "2. Si la registraste después de iniciar Codespaces, reinicia Codespaces.\n"
            "   (En la esquina inferior izquierda: «Codespaces» → «Stop Current Codespace» → volver a abrir)"
        )
    return key
