# AIE2026: repositorio de ejercicios y tareas

Este repositorio se usa para los ejercicios y las tareas de AI Engineering Pilot Course (AIE2026).
A lo largo del curso, iremos desarrollando poco a poco un **agente que ayude a aprender ingeniería de IA**.

## Entorno previsto

Los ejercicios están diseñados para realizarlos **solo con el navegador**. No es necesario instalar nada en tu PC.

| Herramienta | Uso | Consideraciones |
|---|---|---|
| Cuenta **personal** de GitHub | Crear un fork de este repositorio y entregar el trabajo mediante una rama y un PR | Las cuentas administradas por empresas o centros educativos pueden tener restricciones para Codespaces y Copilot |
| GitHub Codespaces | Entorno de desarrollo para Lecture 01, Lecture 03, Lecture 05 y otras sesiones. La configuración de `.devcontainer/` prepara automáticamente un contenedor con Python 3.12, uv y Node.js | La cuota gratuita de una cuenta personal es de 120 horas de núcleo al mes (unas 60 horas con 2 núcleos). **Detén el Codespace al terminar** |
| GitHub Copilot (basta con Free) | Completar código y usar el chat. En la tarea avanzada de Lecture 06 también se usa como cliente MCP | Free tiene límites mensuales para las sugerencias de código y el chat |
| Gemini API (cuota gratuita de Google AI Studio) | Llamar al LLM. Genera la clave con una cuenta **personal** de Google y pásala mediante el secret `GEMINI_API_KEY` de Codespaces | La cuota gratuita tiene límites por minuto y por día (véase «Supuestos y limitaciones» más abajo) |
| Google Colab (GPU T4, cuota gratuita) | Se usa únicamente para el entrenamiento con LoRA de Lecture 02 | El tiempo de uso de la GPU es limitado. Elimina el entorno de ejecución al terminar |

Si prefieres trabajar en tu PC, instala Python 3.12 y [uv](https://docs.astral.sh/uv/), ejecuta `uv sync --frozen` y configura la variable de entorno `GEMINI_API_KEY`.

## Primeros pasos (Lecture 01)

1. Crea un **fork** de este repositorio en tu cuenta
2. Crea una clave de Gemini API en [Google AI Studio](https://aistudio.google.com/apikey)
3. Registra `GEMINI_API_KEY` en **Settings → Codespaces → Secrets** de GitHub y selecciona tu fork como repositorio autorizado
4. En tu fork, selecciona **Code → Codespaces → Create codespace on main**
5. Comprueba que funciona desde el terminal

```bash
uv run pytest -q
uv run python -m app.ask "¿Qué es LoRA?"
```

Consulta las instrucciones detalladas en [lectures/01/problem.md](lectures/01/problem.md).

## Estructura

```
.devcontainer/   Definición del entorno de Codespaces (Python 3.12, uv, Node.js; ejecuta uv sync --frozen al iniciar)
.github/workflows/test.yml  Ejecuta las pruebas con cada PR (en un fork hay que habilitarlas en la pestaña Actions)
app/
  config.py      Lectura del nombre del modelo y de la clave API
  ask.py         Lecture 01: hacer preguntas al LLM
  tools.py       Lecture 03: herramientas del agente (búsqueda en el glosario, etc.)
  agent.py       Lecture 03: agente de apoyo al aprendizaje con Pydantic AI (Lecture 06: mediante MCP con --mcp)
  judge.py       Lecture 04: evaluar casos con un LLM y calcular el acuerdo con etiquetas humanas
  mcp_server.py  Lecture 06: servidor MCP que ofrece el glosario
  mcp_servers.json Lecture 06: configuración de los servidores MCP que se usarán (formato mcpServers)
data/
  glossary.json  Glosario del curso
  lectures/      Puntos clave de cada sesión
  eval/          Lecture 04: conjunto de evaluación (lec04_cases.jsonl) y criterios (rubric.md)
tools/
  annotate.py    Lecture 04: interfaz de etiquetado (Streamlit, añadido temporalmente con uv run --with)
.streamlit/      Configuración de Streamlit para el reenvío de puertos de Codespaces
lectures/NN/
  problem.md     Ejercicios y tareas de la sesión
  answer.md      Archivo que debes completar y entregar
notebooks/       Lecture 02: cuaderno de LoRA para Google Colab (lora_format_tuning.ipynb)
scripts/         Scripts auxiliares
tests/           Pruebas (no requieren clave API)
pyproject.toml / uv.lock  Dependencias y sus versiones fijadas
```

## Cómo entregar el trabajo

1. Crea una rama de trabajo para cada sesión (por ejemplo, `git switch -c lec01`)
2. Realiza los ejercicios y la tarea, y completa `lectures/NN/answer.md`
3. Haz push y crea un PR desde la rama de trabajo hacia `main` **dentro de tu propio fork**

Las tareas tienen tres niveles: «Básico», «Implementación» y «Avanzado». Basta con realizar uno de ellos para completar la tarea.

## Supuestos y limitaciones

- **Las versiones de las dependencias están fijadas** (`uv.lock`: Python 3.12, pydantic-ai-slim 2.57.0, google-genai 2.31.0). No se actualizarán durante el curso. Instálalas con `uv sync --frozen`.
- **El modelo predeterminado es `gemini-3.5-flash-lite`**. Puedes cambiarlo con la variable de entorno `AIE_MODEL` (véase «Cambiar de modelo» más abajo). También puedes usar otros modelos o una API contratada por tu cuenta
- **La cuota gratuita de Gemini API tiene límites de uso**. Los agentes (a partir de Lecture 03) llaman al LLM varias veces por pregunta, por lo que alcanzan el límite antes que en Lecture 01. Si aparece `Se ha alcanzado el límite de uso`, espera aproximadamente 1 minuto. Si se repite `El modelo está saturado (503)`, prueba con `AIE_MODEL=gemini-3.1-flash-lite`
- **Pasa la clave API únicamente mediante la variable de entorno `GEMINI_API_KEY`**. No la pegues en el código, en commits ni en el chat. Si se filtra, elimínala en AI Studio y crea otra
- Codespaces puede acceder a Internet, pero no se puede acceder a su interior desde fuera (el reenvío de puertos es privado de forma predeterminada). El servidor MCP de Lecture 06 se ejecuta dentro de Codespaces
- Las pruebas (`uv run pytest -q`) funcionan sin clave API (usan TestModel, que no llama al LLM)

## Normas que debes respetar

- **No escribas claves API en el código ni en los commits.** Pásalas mediante un secret de Codespaces
- **Detén Codespaces al terminar.** Si agotas la cuota gratuita, no podrás iniciarlo
- Puedes usar herramientas de IA como Copilot. Lee y comprende el código que proponen antes de incorporarlo

## Cambiar de modelo

El modelo predeterminado es `gemini-3.5-flash-lite`. Puedes cambiarlo con la variable de entorno `AIE_MODEL`.

```bash
AIE_MODEL=gemini-3.5-flash uv run python -m app.ask "¿Qué es LoRA?"
```

La cuota gratuita tiene límites de solicitudes por minuto y por día. Consulta los límites en la [página de límites de uso de Gemini API](https://ai.google.dev/gemini-api/docs/rate-limits).
