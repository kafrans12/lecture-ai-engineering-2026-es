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

from pydantic_ai import Agent
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
- Antes de responder sobre términos o detalles específicos del curso, consulta siempre el glosario con search_glossary.
- Usa get_lecture_summary si te preguntan por el contenido de una sesión.
- Si algo no aparece en el glosario, indica «No aparece en el glosario» en lugar de afirmar una suposición.
- Al final de la respuesta, indica la sesión relacionada (Lecture NN).
- Orienta mediante pistas para razonar, sin escribir directamente la solución de la tarea.

- Cuando el usuario solicite un quiz, utiliza make_quiz para generar una pregunta de la sesión indicada.
- Presenta una sola pregunta a la vez y no muestres su respuesta.
- Si el estudiante solicita una primera pista, ofrece una analogía o contexto general relacionado con el concepto, sin mencionar su definición ni sus propiedades distintivas.
- Si solicita una segunda pista, ofrece una relación técnica que permita razonar sobre el concepto, pero no identifiques directamente qué representa el término preguntado. Formula una pregunta orientadora que obligue al estudiante a deducir esa relación por sí mismo.
- Antes de entregar cualquier pista, verifica que el estudiante todavía necesite realizar una inferencia importante para llegar a la respuesta.
- Cuando el estudiante responda, evalúa su explicación, identifica aciertos e imprecisiones y ofrece retroalimentación constructiva.
- No reveles la solución completa salvo que el estudiante la solicite expresamente.
"""

# El modelo se pasa al ejecutar (para sustituirlo en las pruebas por TestModel, que no llama a la API)
agent = Agent(instructions=INSTRUCTIONS)
agent.tool_plain(tools.search_glossary)
agent.tool_plain(tools.get_lecture_summary)

# TODO(Lecture 03: ejercicio): crea make_quiz en tools.py y regístrala aquí
agent.tool_plain(tools.make_quiz)
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
        result = target.run_sync(args.question, model=build_model())
    except ModelHTTPError as e:
        print(api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)
    print(result.output)
    if args.trace:
        print_trace(result)


if __name__ == "__main__":
    main()
