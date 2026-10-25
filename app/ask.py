"""
Lecture 01 - Consultas a Gemini.

Permite realizar una pregunta individual o mantener una conversación
con historial utilizando el modo --chat.
"""

import argparse

from google import genai
from google.genai import errors, types

from app.config import MODEL, api_error_message, get_api_key

# Pregunta específica del curso. La respuesta correcta está en homework-levels de data/glossary.json
DEFAULT_QUESTION = "¿Qué son los «3 niveles» de las tareas del curso AIE2026?"

TEMPERATURE = 0.2

def show_usage(response) -> None:
    """Muestra los tokens utilizados, si están disponibles."""
    usage = response.usage_metadata

    if usage is not None:
        print(f"[Input tokens] {usage.prompt_token_count}")
        print(f"[Output tokens] {usage.candidates_token_count}")

def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(
        model=MODEL, 
        contents=question,
        config=types.GenerateContentConfig(
            temperature=TEMPERATURE
        ),
        
    )

    show_usage(response)
    
    return response.text

def chat_loop(first_question: str | None = None) -> None:
    """Inicia una conversación y conserva el historial durante la sesión."""
    client = genai.Client(api_key=get_api_key())

    chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            temperature=TEMPERATURE
        ),
    )

    print(f"[model] {MODEL}")
    print("[Chat] Conversación iniciada.")
    print("Escribe 'salir', 'exit' o 'quit' para terminar.\n")

    question = first_question

    while True:

        try:
            if question is None:
                question = input("Pregunta: ").strip()
            else:
                print(f"Pregunta: {question}")


        except (KeyboardInterrupt, EOFError):
            print("\nConversación finalizada.")
            break

        if question.lower() in {"salir", "exit", "quit"}:
            print("Conversación finalizada.")
            break

        if not question:
            question = None
            continue

        try:
            response = chat.send_message(question)

            show_usage(response)

            print(f"\nRespuesta: {response.text}\n")

        except errors.APIError as e:
            print(api_error_message(e.code, e.message))

        except KeyboardInterrupt:
            print("\nConversación interrumpida.")
            break

        question = None   



def main() -> None:
    """Procesa los argumentos y ejecuta el modo solicitado."""
    parser = argparse.ArgumentParser(
        description="Hacer preguntas al LLM"
    )
    parser.add_argument(
        "question", 
        nargs="?", 
        default=None
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Iniciar una conversación con historial"
    )

    args = parser.parse_args()

    if args.chat:
        chat_loop(args.question)
        return

    question = (
        args.question 
        if args.question is not None 
        else DEFAULT_QUESTION
    )
    

    print(f"[model] {MODEL}")
    print(f"[Pregunta] {question}\n")

    try:
        print(ask(question))
        
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
