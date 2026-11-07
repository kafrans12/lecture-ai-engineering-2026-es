"""Lecture 06: ofrecer el glosario y los puntos clave de las sesiones mediante un servidor MCP.

Uso:
    uv run python -m app.agent --mcp --list-tools   # Listar las herramientas de este servidor (sin clave API)
    uv run python -m app.mcp_server --http          # Iniciar con Streamable HTTP (http://127.0.0.1:8000/mcp)

Sin argumentos, espera conexiones por stdio (entrada y salida estándar). Está pensado para que un
cliente MCP (--mcp de app.agent o Copilot Chat) lo inicie como subproceso; si lo ejecutas manualmente,
parecerá detenido mientras espera la entrada.

En Lecture 03 registramos directamente las funciones de tools.py en agent.py. Con un servidor MCP,
las mismas funciones pueden usarse mediante un procedimiento común desde otros clientes además de
Pydantic AI, como Copilot Chat.
"""

import argparse

from mcp.server.mcpserver import MCPServer

from app import tools

# Nombre y descripción del servidor, visibles en el cliente (distintos de la clave "glossary" de la configuración)
server = MCPServer(
    "aie2026-glossary",
    instructions="Ofrece el glosario y los puntos clave de las sesiones de AI Engineering Pilot Course (AIE2026).",
)

# Ofrece las mismas funciones de Lecture 03 como herramientas MCP. Los docstrings y las anotaciones de tipos forman la descripción
server.tool()(tools.search_glossary)

# TODO(Lecture 06: ejercicio): expón también tools.get_lecture_summary (igual que en la línea anterior)
# Si creaste make_quiz en Lecture 03, también puedes exponerla


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor MCP del glosario")
    parser.add_argument("--http", action="store_true", help="Iniciar con Streamable HTTP (stdio de forma predeterminada)")
    args = parser.parse_args()
    if args.http:
        print("Iniciando el servidor MCP en http://127.0.0.1:8000/mcp (Ctrl+C para detenerlo)")
        server.run(transport="streamable-http")
    else:
        # Con stdio, la salida estándar es el canal del protocolo: no se debe usar print
        server.run()


if __name__ == "__main__":
    main()
