"""Lecture 03: agente de apoyo al aprendizaje con Pydantic AI.

Uso:
    uv run python -m app.agent "¿Qué es la «etiqueta lecNN-start» que se usa en el curso AIE2026?"
    uv run python -m app.agent --trace "¿Cuál es la diferencia entre LoRA y QLoRA?"  # Mostrar llamadas a herramientas
    uv run python -m app.agent --mcp --trace "¿Qué es LoRA?"    # Lecture 05: recibir herramientas de un servidor MCP
    uv run python -m app.agent --mcp --list-tools               # Lecture 05: listar herramientas que ve el modelo (sin clave API)

Agente = modelo + bucle + herramientas.
El modelo llama a las funciones de tools.py como «herramientas» y elabora la respuesta a partir de sus resultados.
En Lecture 05 recibe las mismas herramientas mediante un servidor MCP (app/mcp_server.py).
"""

import argparse
import inspect
import json
from pathlib import Path

from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults
from pydantic_ai.exceptions import ModelHTTPError
from fastmcp import Client
from pydantic_ai.mcp import MCPToolset, StdioTransport
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.google import GoogleProvider

from app import tools
from app.config import MODEL, api_error_message, get_api_key

INSTRUCTIONS = """\
Eres un agente de apoyo al aprendizaje de AI Engineering Pilot Course (AIE2026).

REGLAS GENERALES:
- Antes de responder sobre términos o detalles específicos del curso, consulta siempre el glosario con search_glossary.
- Usa get_lecture_summary si te preguntan por el contenido de una sesión.
- Si algo no aparece en el glosario, indica «No aparece en el glosario» en lugar de afirmar una suposición.
- Al final de la respuesta, indica la sesión relacionada (Lecture NN).
- Orienta mediante pistas para razonar, sin escribir directamente la solución de la tarea.

QUIZZES Y APRENDIZAJE GUIADO:
- Cuando el usuario solicite un quiz, utiliza make_quiz para generar una pregunta de la sesión indicada.
- Presenta una sola pregunta a la vez y no muestres su respuesta.
- Si el estudiante solicita una primera pista, ofrece una analogía o contexto general relacionado con el concepto, sin mencionar su definición ni sus propiedades distintivas.
- Si solicita una segunda pista, ofrece una relación técnica que permita razonar sobre el concepto, pero no identifiques directamente qué representa el término preguntado. Formula una pregunta orientadora que obligue al estudiante a deducir esa relación por sí mismo.
- Antes de entregar cualquier pista, verifica que el estudiante todavía necesite realizar una inferencia importante para llegar a la respuesta.
- Cuando el estudiante responda, evalúa su explicación, identifica aciertos e imprecisiones y ofrece retroalimentación constructiva.
- No reveles la solución completa salvo que el estudiante la solicite expresamente.

REGISTRO DE APRENDIZAJE (save_learning_log):
- Utiliza save_learning_log únicamente cuando el estudiante solicite explícitamente guardar sus apuntes o registrar un aprendizaje.
- No guardes información automáticamente durante consultas, explicaciones o quizzes.
- Identifica el tema (topic) y los apuntes (notes) a partir de la solicitud del estudiante.
- Conserva fielmente el significado de los apuntes. No inventes información ni agregues conclusiones que el estudiante no haya proporcionado.
- Si falta información esencial para identificar el tema o el contenido, solicita una aclaración antes de intentar guardar.
- No solicites información adicional cuando el tema y los apuntes ya estén suficientemente definidos.
- La herramienta modifica archivos y requiere autorización humana antes de ejecutarse.
- No afirmes que el registro fue guardado mientras la operación esté pendiente de aprobación.
- Si la operación es aprobada y se ejecuta correctamente, confirma que los apuntes fueron guardados.
- Si la operación es rechazada, respeta la decisión del estudiante y no vuelvas a solicitar la misma escritura durante esa interacción.
- Después de un rechazo, informa brevemente que los apuntes no fueron guardados.
- Si ocurre un error al guardar, informa del fallo sin afirmar que la operación fue exitosa.
- No intentes eludir el mecanismo de aprobación ni utilizar otras herramientas para realizar la escritura.
- No afirmes que puedes editar, eliminar o recuperar registros anteriores mediante esta herramienta, porque esas operaciones no están implementadas.
"""



# El modelo se pasa al ejecutar (para sustituirlo en las pruebas por TestModel, que no llama a la API)
agent = Agent(
    instructions=INSTRUCTIONS,
    output_type=[str, DeferredToolRequests],
)
agent.tool_plain(tools.search_glossary)
agent.tool_plain(tools.get_lecture_summary)

# TODO(Lecture 03: ejercicio): crea make_quiz en tools.py y regístrala aquí
agent.tool_plain(tools.make_quiz)
agent.tool_plain(tools.save_learning_log, requires_approval=True)

# Lecture 05: archivo de configuración de servidores MCP. Mismo formato "mcpServers" que Claude Desktop y Cursor
MCP_CONFIG = Path(__file__).resolve().parent / "mcp_servers.json"


def load_mcp_servers(config_path: Path = MCP_CONFIG) -> list[MCPToolset]:
    """Lee la configuración (formato mcpServers) y crea una conexión (MCPToolset) por servidor.

    - Con "command", usa stdio: inicia el servidor como subproceso
    - Con "url", usa Streamable HTTP: conecta con un servidor ya iniciado
    Añade «nombre_del_servidor_» a los nombres de las herramientas (por ejemplo,
    glossary_search_glossary) para distinguir nombres iguales de servidores diferentes.

    Pydantic AI también ofrece load_mcp_toolsets() para lo mismo. Aquí se construyen manualmente
    porque la detección automática del tipo de conexión ("auto") produce muchas advertencias al
    conectar con servidores creados con SDK antiguos, como fetch. Fijar "legacy" permite conectar
    sin esas advertencias tanto con servidores antiguos como con los nuevos.
    """
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))["mcpServers"]
    toolsets = []
    for name, spec in config.items():
        if "url" in spec:
            transport = spec["url"]
        else:
            transport = StdioTransport(spec["command"], spec.get("args", []), env=spec.get("env"))
        toolsets.append(MCPToolset(Client(transport, mode="legacy")).prefixed(name))
    return toolsets


def build_mcp_agent(config_path: Path = MCP_CONFIG) -> Agent:
    """Lecture 05: agente que usa las herramientas de servidores MCP en lugar de registrar funciones directamente. Conserva INSTRUCTIONS."""
    return Agent(instructions=INSTRUCTIONS, toolsets=load_mcp_servers(config_path))


def build_model() -> GoogleModel:
    return GoogleModel(MODEL, provider=GoogleProvider(api_key=get_api_key()))


def print_tools(target: Agent) -> None:
    """Muestra las herramientas que ve el modelo (nombre, descripción y argumentos), sin llamar al LLM.

    Pasa la lista a TestModel (el modelo simulado de las pruebas) y la lee desde él.
    Para el modelo, las herramientas de servidores MCP y las funciones de Lecture 03 tienen la misma forma.
    """
    model = TestModel(call_tools=[])
    target.run_sync("Lista de herramientas", model=model)
    tools_seen = model.last_model_request_parameters.function_tools
    print(f"Herramientas que ve el modelo: {len(tools_seen)}")
    for tool in tools_seen:
        print(f"\n[{tool.name}]")
        print("  " + inspect.cleandoc(tool.description or "").replace("\n", "\n  "))
        params = tool.parameters_json_schema.get("properties", {})
        print(f"  Argumentos: {json.dumps(params, ensure_ascii=False)}")


def print_trace(result) -> None:
    """Muestra qué herramientas se han llamado, con qué argumentos y qué han devuelto."""
    print("\n--- trace ---")
    for message in result.all_messages():
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                print(f"[tool call]   {part.tool_name}({part.args})")
            elif isinstance(part, ToolReturnPart):
                print(f"[tool return] {part.tool_name} -> {str(part.content)[:120]}…")
    print(f"[usage] {result.usage}")

def process_approvals(requests, rejected_tools):
    """Procesa aprobaciones y bloquea herramientas rechazadas en esta ejecución."""
    decisions = {}

    for call in requests.approvals:
        tool_name = call.tool_name

        # Bloquea cualquier reintento de una herramienta rechazada.
        if tool_name in rejected_tools:
            decisions[call.tool_call_id] = False
            print(
                f"\n[Rechazo automático] "
                f"{tool_name}: herramienta previamente rechazada."
            )
            continue

        print(f"\n[Solicitud de aprobación] {tool_name}")
        print(f"Argumentos: {call.args}")

        answer = input("¿Autorizar esta operación? [s/N]: ")
        approved = answer.strip().lower() == "s"

        decisions[call.tool_call_id] = approved

        if not approved:
            rejected_tools.add(tool_name)

        print("[Aprobada]" if approved else "[Rechazada]")

    return decisions

def main() -> None:
    parser = argparse.ArgumentParser(description="Hacer una pregunta al agente de apoyo al aprendizaje")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--trace", action="store_true", help="Mostrar llamadas a herramientas")
    parser.add_argument("--mcp", action="store_true", help="Lecture 05: recibir herramientas de servidores MCP (app/mcp_servers.json)")
    parser.add_argument("--list-tools", action="store_true", help="Mostrar las herramientas que ve el modelo y terminar (sin clave API)")
    args = parser.parse_args()

    target = build_mcp_agent() if args.mcp else agent
    if args.list_tools:
        print_tools(target)
        return
    if not args.question:
        parser.error("Indica una pregunta")

    print(f"[model] {MODEL}")
    if args.mcp:
        print("[tools] Servidores MCP (app/mcp_servers.json)")
    try:
        model = build_model()
        result = target.run_sync(args.question, model=model)

        max_approval_rounds = 3
        approval_rounds = 0
        rejected_tools = set()

        while isinstance(result.output, DeferredToolRequests):
            approval_rounds += 1

            if approval_rounds > max_approval_rounds:
                raise RuntimeError(
                    "Se alcanzó el límite de rondas de autorización."
                )
            requests = result.output

            if requests.calls:
                raise RuntimeError(
                    "Hay llamadas diferidas que este CLI todavía no gestiona."
                )

            if not requests.approvals:
                raise RuntimeError(
                    "El agente devolvió una solicitud diferida sin aprobaciones."
                )

            decisions = process_approvals(
                requests,
                rejected_tools,
            )

            result = target.run_sync(
                "Continúa con el resultado de la autorización.",
                model=model,
                message_history=result.all_messages(),
                deferred_tool_results=DeferredToolResults(
                    approvals=decisions
                ),
            )

    except ModelHTTPError as e:
        print(api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)

    print(result.output)

    if args.trace:
        print_trace(result)


if __name__ == "__main__":
    main()
