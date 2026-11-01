# Lecture 03: ejercicios y tarea — crear un agente de apoyo al aprendizaje

## Objetivos de esta sesión

- Comprobar en tu propio código que un agente consta de «modelo + bucle + herramientas»
- Leer qué herramientas se han llamado y con qué argumentos
- Añadir una herramienta

## Ejercicios (30 minutos)

Dedicaremos los primeros cinco minutos aproximadamente a explicar la tarea de Lecture 02. Mientras tanto, pulsa Sync fork en el paso 1 e inicia Codespaces (tarda unos minutos en arrancar).

### 1. Incorporar las actualizaciones del repositorio del curso y crear la rama lec03

Incorpora las actualizaciones del repositorio del curso a tu fork antes de crear una rama de trabajo.

1. Abre tu fork en GitHub y pulsa **Sync fork → Update branch** (si ya está actualizado, no aparecerá Update branch y no tendrás que hacer nada)
2. Inicia Codespaces y ejecuta lo siguiente en la terminal

```bash
git switch main
git pull --no-rebase
git switch -c lec03
```

- Si `git switch main` se detiene, quedan cambios sin confirmar en la rama de la sesión anterior. Haz commit de ellos en esa rama y vuelve a intentarlo
- Si aparece `a branch named 'lec03' already exists`, ya has creado `lec03`. Cambia a ella con `git switch lec03`
- Si `git pull --no-rebase` muestra `CONFLICT`, ejecuta `git merge --abort` para volver al estado anterior y empieza con el método siguiente (al abortar la fusión, se conservan tus cambios)

#### Si main no funciona o no has terminado el trabajo de las sesiones anteriores

Si Sync fork muestra un conflicto y propone crear un Pull Request o seleccionar «Discard commits», **no pulses esas opciones** y empieza con el método siguiente. «Discard commits» elimina tus propios commits.

Crea una rama a partir del código inicial del repositorio del curso (la etiqueta `lec03-start`).

```bash
git fetch https://github.com/matsuolab/lecture-ai-engineering-2026.git tag lec03-start
git switch -c lec03 lec03-start
```

### 2. Hacer al agente la misma pregunta que en Lecture 01

```bash
uv run python -m app.agent "¿Qué son los «3 niveles» de las tareas del curso AIE2026?"
```

Compara la respuesta con la de `app.ask` en Lecture 01. El agente consulta el glosario antes de responder. La información correcta está en la entrada `homework-levels` de `data/glossary.json`.

### 3. Leer las llamadas a herramientas

```bash
uv run python -m app.agent --trace "¿Cuál es la diferencia entre LoRA y QLoRA?"
```

En las líneas `[tool call]`, comprueba qué herramienta llamó el modelo y con qué argumentos. `requests`, dentro de `[usage]`, indica cuántas llamadas al LLM se hicieron para una pregunta.

Las instrucciones al modelo explican por qué debe buscar antes de responder y consultar los términos de uno en uno. Están en dos lugares:

- `INSTRUCTIONS` de `app/agent.py` (alrededor de la línea 31): instrucciones para todo el agente, como «consulta siempre el glosario con search_glossary» y «Al final de la respuesta, indica la sesión relacionada (Lecture NN)»
- La docstring de cada herramienta en `app/tools.py`: se entrega al modelo como descripción de la herramienta. La de `search_glossary` indica que se debe poner un solo término en `query`

En el nivel Básico de la tarea, modificarás estas instrucciones y compararás cómo cambia el comportamiento.

### 4. Escribir y registrar la herramienta make_quiz

Permite que el agente cree una pregunta a partir del glosario cuando se le pida una pregunta de repaso de Lecture 02. El modelo llama a `make_quiz` con `lecture=2`; la herramienta elige un término de Lecture 02 y devuelve una pregunta y su respuesta, que el modelo utiliza para plantear la pregunta.

1. Añade la función `make_quiz(lecture: int) -> str` a `app/tools.py`
2. Escribe una docstring que explique cuándo y para qué se usa la herramienta (el modelo la lee para decidir si debe usarla)
3. Recoge del glosario (`load_glossary()`) los términos cuyo campo `lecture` corresponda a la sesión solicitada y elige uno (por ejemplo, con `random.choice`)
4. Devuelve una cadena que contenga una pregunta como «¿Qué significa este término?» y la respuesta (la `definition` del término), por ejemplo usando `json.dumps`
5. Regístrala con `agent.tool_plain(tools.make_quiz)` en `TODO(Lecture 03: ejercicio)` de `app/agent.py`

Ejemplo del valor devuelto por `make_quiz(2)`:

```text
{"question": "¿Qué significa PEFT?", "answer": "En lugar de todos los parámetros del modelo, …"}
```

### 5. Comprobar que se llama a make_quiz

```bash
uv run python -m app.agent --list-tools    # Herramientas visibles para el modelo (no requiere clave API)
uv run python -m app.agent --trace "Hazme una pregunta de repaso de Lecture 02"
uv run pytest -q
```

Si la lista incluye `make_quiz` y tu docstring, y aparece una línea como `[tool call] make_quiz({'lecture': 2})`, lo has conseguido.

Sin usar una clave API, `uv run pytest -q` llama a todas las herramientas, incluida la `make_quiz` que has añadido, con argumentos ficticios (como `lecture=0`) y comprueba que no fallen con un error. Lecture 0 no existe, así que la prueba fallará si no has previsto el caso de que no haya términos. En ese caso, haz que la herramienta devuelva un mensaje claro cuando no encuentre términos.

- No aparece en la lista → no está registrada en `app/agent.py`
- Aparece, pero no se llama → describe un caso de uso concreto en la docstring. Añade a `INSTRUCTIONS` algo como «Usa make_quiz cuando se pida una pregunta de repaso»

### 6. Entregar y detener Codespaces

Completa `lectures/03/answer.md` y crea un PR de `lec03` hacia `main` en tu propio fork. **Comprueba que base repository sea tu propio fork.**

```bash
git add -A
git commit -m "Lecture 03 exercises"
git push -u origin lec03
```

Si no terminas el paso 4, puedes entregar los resultados hasta el paso 3. Si continúas trabajando, haz push a la misma rama para actualizar el PR.

Por último, selecciona «Codespaces» en la esquina inferior izquierda → **Stop Current Codespace**.

## Tarea (basta con completar un nivel)

Elige uno de los tres niveles: Básico, Implementación o Avanzado. Basta con trabajar en uno de ellos para completar la tarea.

| Nivel | Contenido |
|---|---|
| Básico | Modifica `INSTRUCTIONS` de `app/agent.py` o las docstrings de las herramientas en `app/tools.py`, que has visto en los ejercicios. Ejecuta la misma pregunta con `--trace`, compara cómo cambian las llamadas a herramientas y las respuestas, y registra los resultados |
| Implementación | Crea la herramienta `save_learning_log` para guardar registros de aprendizaje en `learning_log/`. Como guardar es una operación difícil de deshacer, pide confirmación al usuario antes de hacerlo (`requires_approval=True` de Pydantic AI) |
| Avanzado | Elige una opción: (a) Conserva las mismas instrucciones y herramientas del agente de los ejercicios, reescribe solo la parte que construye el agente con ADK de Google, ejecútalo con `adk run` y compara el código y las respuestas. (b) Ejecuta el agente de programación Pi en Codespaces y compara su prompt de sistema público con `INSTRUCTIONS` de tu agente |

Escribe la entrega en la sección «Tarea» del mismo `lectures/03/answer.md` que usaste para los ejercicios.

### Cómo abordar el nivel Básico

Modifica solo uno de los dos lugares que viste en el paso 3 de los ejercicios cada vez. Ejecuta la misma pregunta con `--trace` y compara los resultados.

- `INSTRUCTIONS` de `app/agent.py` (alrededor de la línea 31): instrucciones para todo el agente
- La docstring de cada herramienta en `app/tools.py`: se entrega al modelo como descripción de la herramienta

Por ejemplo, prueba los cambios siguientes. Registra cómo cambian las herramientas elegidas, el número de llamadas, los argumentos y las respuestas.

- Si eliminas de `INSTRUCTIONS` la indicación de consultar siempre el glosario con `search_glossary`, ¿responde sin buscar?
- Si cambias la docstring de `search_glossary` de «Pon un solo término en query» a «Pon varios términos juntos», ¿cómo cambian el número de búsquedas y los argumentos?
- Si sustituyes «Al final de la respuesta, indica la sesión relacionada (Lecture NN)» en `INSTRUCTIONS` por otra instrucción (por ejemplo, «Termina con una pregunta de repaso»), ¿cómo cambia la respuesta?

### Cómo abordar el nivel Implementación

1. Crea `save_learning_log` en `app/tools.py` y regístrala en `app/agent.py` con `requires_approval=True`
2. Cuando el modelo llama a esta herramienta, la ejecución se detiene a la espera de aprobación y devuelve `DeferredToolRequests` como resultado (`result.output`). Por ello, añade `DeferredToolRequests` a `output_type` del agente (de lo contrario, se produce un error)

   ```python
   from pydantic_ai import Agent, DeferredToolRequests

   agent = Agent(instructions=INSTRUCTIONS,
                 output_type=[str, DeferredToolRequests])
   ```

3. En la CLI, pregunta al usuario si permite guardar para cada llamada de `result.output.approvals`. Pasa esas decisiones (`DeferredToolResults`) y la conversación hasta ese momento (`message_history=result.all_messages()`) a una nueva llamada a `run_sync`

Para más detalles, consulta Human-in-the-Loop Tool Approval en la documentación oficial de Pydantic AI, «Deferred Tools»: https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/

### Cómo abordar la opción avanzada (a): reescribir con ADK

Usa las mismas instrucciones y herramientas del agente de los ejercicios y reescribe solo la parte que construye el agente con ADK.

| Alcance | Contenido |
|---|---|
| Reutilizar | `INSTRUCTIONS` de `app/agent.py`, y `search_glossary` y `get_lecture_summary` de `app/tools.py` (también `make_quiz` si la creaste en los ejercicios) |
| Escribir | Crea `agent.py` (el código siguiente) y `__init__.py` (con la única línea `from . import agent`) en `adk_agent/glossary_agent/` |
| No hace falta | Funciones de comandos como `--trace`, pruebas ni herramientas que requieran aprobación. No modifiques los archivos de `app/` |
| Comparar | El código (cómo se proporcionan las instrucciones y herramientas) y las respuestas a las mismas preguntas de los ejercicios |

Estructura de `adk_agent/glossary_agent/agent.py`:

```python
from google.adk.agents import Agent
from app import tools
from app.agent import INSTRUCTIONS

root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[...],  # Herramientas utilizadas en los ejercicios
)
```

Para ejecutarlo, usa este comando desde la raíz del repositorio:

```bash
PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
```

- `adk run` permite conversar desde la terminal. Escribe una pregunta y pulsa Enter para recibir una respuesta. Para terminar, escribe `exit`
- `uv run --with google-adk` añade ADK temporalmente al entorno del curso para esta ejecución. No cambia `pyproject.toml` ni `uv.lock`
- `PYTHONPATH=.` permite importar la carpeta `app` desde la raíz del repositorio
- Se utiliza la clave API del secreto de Codespaces `GEMINI_API_KEY` que ya tienes configurado
- La primera descarga de ADK tarda aproximadamente un minuto

Haz las mismas preguntas que en los ejercicios y registra las diferencias en el código y las respuestas respecto a la versión con Pydantic AI.

ADK 2.0 introdujo cambios importantes. Algunos artículos de Internet pueden contener información antigua que no los refleje, así que consultar la documentación oficial ayudará a evitar errores al implementarlo.

- Documentación oficial: https://adk.dev/

### Cómo abordar la opción avanzada (b): ejecutar Pi en Codespaces

Pi es un agente de programación que modifica archivos y ejecuta comandos sin pedir confirmación. Pruébalo dentro de Codespaces, no en tu propio PC.

1. **Instalar**: ejecuta lo siguiente en la terminal de Codespaces

   ```bash
   npm install -g --ignore-scripts @earendil-works/pi-coding-agent
   ```

2. **Iniciar**: escribe `pi` en la terminal
3. **Configurar el modelo**: dentro de Pi, escribe `/model` y elige un modelo de Gemini. Se utiliza la clave API del secreto de Codespaces `GEMINI_API_KEY` existente
4. **Comparar**: el prompt de sistema de Pi está en `packages/coding-agent/src/core/system-prompt.ts` del repositorio público https://github.com/earendil-works/pi. Compáralo con tus `INSTRUCTIONS` para ver qué incluye y qué omite

- Documentación oficial de Pi: https://github.com/earendil-works/pi/tree/main/packages/coding-agent/docs

## Referencias

- Pydantic AI: https://pydantic.dev/docs/ai/
- ADK: https://adk.dev/
