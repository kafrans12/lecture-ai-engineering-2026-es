# Lecture 06: ejercicios y tarea — usar las herramientas mediante un servidor MCP

## Objetivos de esta sesión

- Separar las herramientas creadas en Lecture 03 en un **servidor MCP** y usarlas desde el mismo agente **a través de MCP**
- Leer «los nombres, las descripciones y los argumentos de las herramientas» que ve el modelo
- Añadir herramientas externas ya existentes **con solo modificar el archivo de configuración**

## Preparación

Si has terminado el trabajo de las sesiones anteriores, crea la rama `lec06` desde `main`.
A partir de esta sesión hay más dependencias, así que ejecuta una vez `uv sync --frozen`.

```bash
git switch main && git switch -c lec06
uv sync --frozen
```

Si no has terminado, puedes crear una rama desde el código inicial de esta sesión en el repositorio del curso (etiqueta `lec06-start`).

```bash
git remote -v                     # Si no existe upstream, añádelo con la siguiente línea
git remote add upstream https://github.com/matsuolab/lecture-ai-engineering-2026.git
git fetch upstream --tags
git switch -c lec06 lec06-start
uv sync --frozen
```

## Ejercicios (30 minutos)

### 1. Listar las herramientas que ve el modelo

```bash
uv run python -m app.agent --list-tools          # Lecture 03: herramientas registradas directamente como funciones
uv run python -m app.agent --mcp --list-tools    # Lecture 06: herramientas recibidas de un servidor MCP
```

Ambos comandos funcionan sin clave API porque no llaman al LLM.
El segundo inicia como subproceso el servidor (`app/mcp_server.py`) indicado en `app/mcp_servers.json` y muestra los nombres, las descripciones y los argumentos de las herramientas que ofrece.

- Comprueba que los nombres llevan el **prefijo «nombre_del_servidor_»**, como en `glossary_search_glossary`. Así se distinguen las herramientas que tienen el mismo nombre en servidores diferentes
- Las descripciones son los propios docstrings de `app/tools.py`. **Para el modelo, las herramientas de función y las herramientas MCP tienen la misma forma**

### 2. Usarlas desde el agente a través de MCP

```bash
uv run python -m app.agent --mcp --trace "¿Qué son los «3 niveles» de las tareas del curso AIE2026?"
```

Compáralo con Lecture 03 (sin `--mcp`) y observa las diferencias en las respuestas, los nombres de las herramientas y el número de `requests`.
Internamente, `build_mcp_agent()` de `app/agent.py` lee el archivo de configuración, inicia los servidores y entrega las herramientas al agente.

### 3. Exponer una herramienta

En el lugar marcado como `TODO(Lecture 06: ejercicio)` de `app/mcp_server.py`, expón también `get_lecture_summary` mediante MCP (una sola línea, igual que para `search_glossary`).

```bash
uv run python -m app.agent --mcp --list-tools
uv run python -m app.agent --mcp --trace "¿Qué se aprende en Lecture 02?"
uv run pytest -q
```

Comprueba que `glossary_get_lecture_summary` aparece en `--list-tools` y que se llama en `--trace`.
Si creaste `make_quiz` en Lecture 03, también puedes exponerla de la misma forma.

### 4. Añadir una herramienta externa ya existente mediante la configuración

Añade a `app/mcp_servers.json` el **servidor fetch** público (obtiene la página de una URL y la devuelve en Markdown). No hace falta escribir código.

```json
{
  "mcpServers": {
    "glossary": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    }
  }
}
```

```bash
uv run python -m app.agent --mcp --list-tools
uv run python -m app.agent --mcp --trace "Resume en español y en 3 líneas el inicio de https://modelcontextprotocol.io/"
```

- La primera vez, `uvx` descarga el servidor, por lo que el inicio tarda unos 10 segundos
- Si aparece `fetch_fetch({'url': ...})` en `--trace`, **el Codespace está accediendo realmente a la URL que ha elegido el modelo**. Antes de añadir una herramienta externa, debes comprender adónde envía datos y qué envía
- `INSTRUCTIONS` se escribió pensando en el glosario. Si fetch no se llama al preguntar por una URL, prueba a añadir a `INSTRUCTIONS` una línea como «Si recibes una URL, lee su contenido con fetch»

### 5. Entregar el trabajo

Completa `lectures/06/answer.md` y crea un PR de `lec06` hacia `main` de tu propio fork.

## Tarea (basta con completar un nivel)

| Nivel | Contenido |
|---|---|
| Básico | Inicia el servidor con `uv run python -m app.mcp_server --http`, cambia `glossary` en el archivo de configuración por `{"url": "http://127.0.0.1:8000/mcp"}` y haz la misma pregunta. Registra las diferencias entre stdio y Streamable HTTP en la forma de inicio, los procesos y los puertos. Compara también cómo cambian `--list-tools` y las llamadas al modificar los docstrings de las herramientas |
| Implementación | Añade al servidor MCP `make_quiz` de Lecture 03 (o una herramienta nueva si no la tienes) y añade pruebas con TestModel en `tests/test_mcp_server.py`. Incluye una comprobación del rango de argumentos (por ejemplo, devolver un mensaje claro si la sesión no existe) y observa con `--trace` cómo ve el modelo los errores a través de MCP |
| Avanzado | Usa el mismo servidor de glosario desde **Copilot Chat** (el cliente MCP de VS Code; instrucciones más abajo). Comprueba que «un servidor se puede usar desde distintos clientes» y compara su uso con el del agente (`app/agent.py`). Registra las diferencias en el proceso hasta que se llama a una herramienta: quién inicia el servidor, si hay aprobación humana antes de la llamada y cómo se presentan los resultados |

### Cómo realizar el nivel avanzado

Copilot Chat es un cliente MCP de VS Code. Al crear `.vscode/mcp.json` en el repositorio, puedes usar las herramientas del servidor en el modo **Agent** del chat (el formato usa `servers`, en lugar del `mcpServers` de `app/mcp_servers.json`; los comandos se ejecutan en la carpeta de trabajo, es decir, la raíz del repositorio).

```json
{
  "servers": {
    "aie-glossary": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    }
  }
}
```

1. Crea el archivo anterior en VS Code de Codespaces. Si aparece **Start** encima de `servers`, púlsalo (si no aparece, abre la paleta de comandos y selecciona **MCP: List Servers** → `aie-glossary` → Start). El servidor se inicia dentro del Codespace
2. Abre Copilot Chat y selecciona el modo **Agent**. Comprueba que en la lista de herramientas (🔧) aparece `search_glossary` de `aie-glossary` (y también `get_lecture_summary` si terminaste el ejercicio 3)
3. Pregunta «¿Qué son los 3 niveles de las tareas de AIE2026?». Si pide confirmación (**Continue**) antes de ejecutar la herramienta, autorízala y comprueba que llama a la herramienta del glosario y usa el resultado para responder
4. En `answer.md`, presenta una junto a otra las llamadas a herramientas que muestra el chat y la salida de `uv run python -m app.agent --mcp --trace`
5. Puedes incluir `.vscode/mcp.json` en el PR (sin información secreta como claves API)

- El modo Agent y MCP también están disponibles en Copilot Free. Sin embargo, el chat tiene un límite mensual, así que haz solo unas pocas pruebas
- En Copilot administrado por una empresa o un centro educativo (Business / Enterprise), las políticas de la organización pueden deshabilitar MCP. Pruébalo con una cuenta personal

## Precauciones

- Un servidor MCP es un **programa que ejecuta código**. No añadas servidores de procedencia desconocida al archivo de configuración
- El servidor fetch accede a las URL elegidas por el modelo. No le pases URL internas de tu organización ni URL que contengan datos personales
- Cuantas más herramientas añadas, más descripciones recibe el modelo y mayores son el número de tokens por llamada y la dificultad para elegir la herramienta adecuada. Usa `--list-tools` para saber cuántas herramientas estás pasando

## Referencias

- Sitio oficial de MCP: https://modelcontextprotocol.io/
- Cliente MCP de Pydantic AI: https://pydantic.dev/docs/ai/mcp/client/
- SDK de Python para MCP (cómo crear servidores): https://github.com/modelcontextprotocol/python-sdk
- Servidores MCP públicos: https://github.com/modelcontextprotocol/servers
- Usar servidores MCP en VS Code: https://code.visualstudio.com/docs/copilot/customization/mcp-servers
