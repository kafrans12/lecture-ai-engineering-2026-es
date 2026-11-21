"""Lecture 01: script para hacer una sola pregunta a un LLM sin herramientas.

Uso:
    uv run python -m app.ask "¿Qué es LoRA?"
    uv run python -m app.ask            # Sin pregunta, se hace una específica del curso

Llamada directa, sin herramientas ni historial de conversación.
Comprueba que, ante detalles específicos del curso, responde «No lo sé» o da
una respuesta general convincente (que no coincide con la realidad del curso).
(En Lecture 03 lo mejoraremos con un agente capaz de buscar en el glosario.)
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# Pregunta específica del curso. La respuesta correcta está en homework-levels de data/glossary.json
DEFAULT_QUESTION = "¿Qué son los «3 niveles» de las tareas del curso AIE2026?"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    # TODO(Lecture 01: ejercicio): usa response.usage_metadata para
    #   mostrar el número de tokens de entrada y de salida (puedes pedir ayuda a Copilot)

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="Hacer una pregunta al LLM sin herramientas")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[Pregunta] {args.question}\n")
    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
