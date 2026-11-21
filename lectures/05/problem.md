# Lecture 05: ejercicios y tarea — responder buscando en los materiales de clase

La base de búsqueda incluida abarca 214 páginas de los materiales principales de Lecture 01–03. Reutiliza los vectores de la fuente japonesa y devuelve los textos traducidos. El modo de contexto completo abarca 8 documentos y 398 páginas, incluidos los ejercicios de las clases 01 y 02.

## Objetivos de esta sesión

- Ejecutar respuestas con todos los materiales y con búsqueda, y comparar respuestas, evidencias, tiempo y número de tokens
- Explicar los datos que usan una página por fragmento y las diferencias entre la búsqueda vectorial, Tree y Graph
- Mejorar la recuperación para tu caso de uso y comprobar el cambio con las mismas preguntas

Usaremos la estructura de «modelo + bucle + herramientas» de Lecture 03 y cambiaremos cómo se recuperan los materiales de clase. A partir de la evaluación de Lecture 04, comprobarás por tu cuenta la corrección de las respuestas y las evidencias de las páginas citadas.

## Materiales y código

| Archivo | Contenido |
|---|---|
| [data/rag_data/lectures.json](../../data/rag_data/lectures.json) | Títulos y textos organizados por sesión, capítulo y página. Cada página se usa como un fragmento |
| [data/rag_data/tree.json](../../data/rag_data/tree.json) | Jerarquía de materiales, capítulos y páginas |
| [data/rag_data/graph.json](../../data/rag_data/graph.json) | Nodos de páginas, términos y otros elementos, y sus relaciones |
| [data/rag_data/index.sqlite3](../../data/rag_data/index.sqlite3) | Base de datos de búsqueda con las 214 páginas de los materiales principales de Lecture 01–03 |
| [scripts/build_rag_index.py](../../scripts/build_rag_index.py) | Genera representaciones vectoriales de los materiales y crea la base de datos SQLite para búsquedas |
| [app/retrieval.py](../../app/retrieval.py) | Búsqueda vectorial, exploración Tree y Graph, y procesamiento con todos los materiales |
| [app/tools.py](../../app/tools.py) | Descripciones, entradas y salidas de las herramientas que usa el modelo |
| [app/agent.py](../../app/agent.py) | Instrucciones, registro de herramientas y selección del modo de ejecución |
| [app/config.py](../../app/config.py) | Materiales seleccionados, número de resultados y alcance de la exploración Graph, entre otros ajustes |

**Alcance actual**: la búsqueda vectorial, Tree y Graph usan las 214 páginas de los materiales principales de Lecture 01–03. El modo de contexto completo utiliza los 8 documentos y las 398 páginas que contiene el JSON de esta versión. En este ejercicio observaremos las distintas formas de recuperar información. Para comparar el rendimiento de los métodos en las mismas condiciones, iguala primero los materiales utilizados.

## Preparación previa

### 1. Incorporar la actualización de Lecture 05 y crear la rama lec05

En tu fork, elige **Sync fork → Update branch** para actualizar `main`. Abre el terminal de Codespaces y ejecuta los comandos de abajo para crear tu rama de trabajo.

```bash
git switch main
git pull --no-rebase
git switch -c lec05
uv sync --frozen
```

- Si ya existe `lec05`, cambia a ella con `git switch lec05`
- Si no puedes cambiar de rama porque quedan modificaciones de la sesión anterior, haz commit en esa rama y vuelve a intentarlo
- Si aparecen conflictos al actualizar, consulta al docente sin descartar tus cambios

Usa la misma variable de entorno `GEMINI_API_KEY` de Lecture 01. Si registraste el secret después de iniciar Codespaces, reinicia el Codespace. Consulta la configuración en el [README](../../README.md).

### 2. Comprobar la base de datos de búsqueda incluida

La búsqueda vectorial y Graph usan directamente `data/rag_data/index.sqlite3`. Una vez incorporada la actualización de Lecture 05, puedes pasar al ejercicio. La vectorización de las preguntas y la generación de respuestas usan `GEMINI_API_KEY`. Tree y el modo de contexto completo no necesitan la base de datos de búsqueda.

## Ejercicios

### PASO 1: proporcionar todos los materiales a la vez

Primero guarda en una variable del mismo terminal la pregunta que compararás. Usa esta misma pregunta con todos los métodos siguientes.

```bash
AIE_QUESTION='Según Lecture 02, ¿qué mantiene fijo LoRA y qué entrena? ¿Qué añade QLoRA?'
uv run python -m app.agent --full-context --trace "$AIE_QUESTION"
```

Registra en [answer.md](answer.md) la respuesta, las páginas citadas y los valores de `[time]`, `[usage]` y `[cost]` que aparecen al final.

El modo de contexto completo también puede responder correctamente. Observa los resultados sin presuponer que fallará. Registra por separado los errores por superar el límite de entrada y los casos en que la entrada se acepta pero el modelo no usa las evidencias necesarias.

### PASO 2: examinar solo los resultados de búsqueda

```bash
uv run python -m app.retrieval "LoRA QLoRA diferencias"
```

Se recuperan hasta 5 páginas cercanas a la pregunta, sin usar el agente. Se muestran el nombre de la sesión, el capítulo, el título de la página, el número de página del PDF y el texto.

- ¿Aparecen páginas que respalden la respuesta, como `lec02-main-p052`?
- ¿Puedes distinguir entre páginas que solo contienen términos similares y páginas que aportan evidencias para responder?

Abre el JSON de los materiales en el editor y busca, por ejemplo, `lec02-main-p052` para consultar el texto de esa página.

### PASO 3: responder usando los resultados de búsqueda

```bash
uv run python -m app.agent --trace "$AIE_QUESTION"
```

En el modo predeterminado responde un agente con `search_materials(query)`. El modelo elige la consulta y responde usando el texto recuperado.

- Comprueba la consulta y el número de llamadas a herramientas en `[tool call]`
- Comprueba que cada cita respalde la explicación. La referencia señala la página traducida cuando se ha verificado, o la página del original japonés de la que procede el texto.
- Distingue entre no recuperar las evidencias necesarias y recuperarlas sin utilizarlas correctamente

Algunas preguntas se resuelven solo con las evidencias de p.52. Aumentar el número de páginas citadas no es un objetivo en sí mismo.

### PASO 4: responder a la misma pregunta con Tree y Graph

Tree selecciona las páginas recorriendo el índice de contenidos.

```bash
uv run python -m app.agent --tree --trace "$AIE_QUESTION"
```

Solo usa `browse_tree(node_id)`. Empieza obteniendo la lista de sesiones y avanza por sesiones, capítulos y páginas con los ID devueltos. Las páginas de `children` solo incluyen la primera frase; al indicar un ID de página, `node.content` contiene el texto completo. Si una página no tiene puntuación de fin de frase, el texto de vista previa es su primera línea. En la traza, comprueba las entradas del índice elegidas y las páginas cuyo texto completo se recuperó.

Graph encuentra puntos de entrada con la búsqueda vectorial y amplía los candidatos a su alrededor.

```bash
uv run python -m app.agent --graph --trace "$AIE_QUESTION"
```

Usa `search_graph(query)`. Parte de las 3 páginas mejor situadas en la búsqueda, recorre relaciones entre páginas adyacentes y términos comunes hasta un máximo de 2 saltos (hops), y devuelve el texto de hasta 10 páginas, incluidos los puntos de entrada. Pasar a una página adyacente requiere 1 salto; pasar a otra página a través de un término requiere 2. Compartir términos no garantiza que una página contenga la respuesta.

Registra cómo cambian la respuesta, las evidencias citadas, el tiempo y los tokens de entrada entre Tree y Graph.

### PASO 5: comparar y registrar los resultados

Resume los resultados de cada método en la tabla de `answer.md`.

| Indicador | Significado |
|---|---|
| `[time]` | Segundos hasta completar la respuesta, incluidos búsqueda y vectorización |
| `[usage]` | Total de tokens de entrada y salida y número de respuestas del modelo para una pregunta |
| `[cost]` | Coste estimado de la API de generación. No incluye la vectorización de la consulta ni la creación del índice |

Si el coste aparece como «No calculable», regístralo así; no lo trates como 0.

Si tienes tiempo, cambia la pregunta y repite la comparación. Si comparas varias preguntas, conserva los resultados de cada una por separado.

| Tipo | Ejemplo de pregunta | Evidencias que comprobar |
|---|---|---|
| Varias páginas | En los ejemplos de Lecture 03, ¿qué diferencia hay entre la compactación y la memoria entre sesiones? ¿Todas las notas diarias pasan a la memoria a largo plazo? | `lec03-main-p013`, `lec03-main-p039`, `lec03-main-p040` |
| Ausente de los materiales | Indica el tiempo medio de respuesta y la tasa de acierto medidos para el sistema RAG que acabamos de crear | Los materiales de clase no contienen registros de mediciones de este sistema |

### PASO 6: entregar y detener Codespaces

Escribe los resultados en `lectures/05/answer.md` y crea un PR desde tu rama de trabajo hacia `main` de tu propio fork. **Comprueba que base repository sea tu propio fork.**

```bash
git add lectures/05/answer.md
# Si has cambiado código, añade también esos archivos con git add
git commit -m "Lecture 05 exercises and homework"
git push -u origin lec05
```

Excluye de los commits las claves API y las bases de datos de búsqueda de tus experimentos. Al terminar, selecciona «Codespaces» en la esquina inferior izquierda → **Stop Current Codespace**.

## Tarea (basta con completar un nivel)

Elige Básico, Implementación o Avanzado. **Basta con realizar uno.** En el apartado «Tarea» del mismo `answer.md`, indica el nivel, qué hiciste, los resultados y tus observaciones o dudas.

| Nivel | Contenido |
|---|---|
| Básico | Cambia una cosa: las instrucciones, la descripción de una herramienta o el número de resultados. Ejecuta la misma pregunta con `--trace` y compara antes y después |
| Implementación | Mejora un aspecto de la recuperación, por ejemplo añadiendo el texto de las páginas adyacentes a los resultados, y compáralo con la búsqueda normal |
| Avanzado | Mejora Tree, Graph o una combinación. Elige las preguntas que quieres resolver y compáralo con RAG básico usando las mismas preguntas |

### Cómo realizar el nivel básico

Cambia solo uno de los siguientes puntos cada vez.

- `INSTRUCTIONS` de `app/agent.py`; para Tree o Graph, `TREE_INSTRUCTIONS` o `GRAPH_INSTRUCTIONS`, respectivamente
- El docstring de una herramienta en `app/tools.py`
- `RAG_TOP_K` de `app/config.py`, que determina cuántos resultados devuelve la búsqueda vectorial normal

Usa la misma pregunta, modelo y materiales. Observa cómo cambian las llamadas a herramientas, sus argumentos y frecuencia, la respuesta y las evidencias citadas. Registra también el tiempo, los tokens y el coste estimado de la API de generación. Estos cambios no requieren reconstruir el índice.

### Cómo realizar el nivel de implementación

Por ejemplo, modifica `app/retrieval.py` para devolver también el texto de 1 página anterior y 1 posterior a cada resultado.

1. Usa la información de `load_pages()` para buscar las páginas adyacentes dentro del mismo `document_id` del resultado
2. Evita devolver páginas duplicadas e incluye tanto el texto como los datos de cita
3. Ejecuta las mismas preguntas que antes y observa casos donde añades evidencias necesarias y casos donde solo aumenta la información innecesaria
4. Registra la implementación, la comparación y los fallos que persisten

También puedes mejorar otro aspecto de la recuperación según tus necesidades. Si solo cambias el alcance de lo recuperado, sin modificar el texto ni los ajustes de vectorización, no necesitas reconstruir el índice.

Si cambias el texto de los materiales o los ajustes de vectorización, sigue el [procedimiento del README](../../README.md#lecture-05-rag): indica primero una base de datos experimental con `AIE_RAG_DB` y después crea el índice.

### Cómo realizar el nivel avanzado

1. Elige las preguntas que quieres resolver. Comprueba primero qué páginas respaldan la respuesta, por ejemplo para explicar un tema entre capítulos o comparar términos relacionados
2. Diseña la recuperación: puedes cambiar cómo Tree presenta el índice y las vistas previas, los tipos de relaciones, saltos o selección de candidatos de Graph, o combinar varios métodos
3. Explica la estructura y el almacenamiento de los datos, el método de búsqueda y por qué los elegiste
4. Compara con RAG básico usando las mismas preguntas, modelo y materiales. Registra respuestas, evidencias citadas, tiempo, tokens y coste estimado de la API de generación
5. Incluye ejemplos de mejoras y de fallos, y analiza si adoptarías el método para tu caso de uso

Puedes usar herramientas de IA. Describe lo que hayas ejecutado y comprobado personalmente. Sigue las indicaciones del curso sobre el plazo de entrega.

## Si algo falla

| Síntoma | Qué comprobar |
|---|---|
| No se encuentra `GEMINI_API_KEY` | Comprueba que registraste el secret de Codespaces y que reiniciaste el Codespace si lo añadiste después |
| «No se encuentra la base de datos de búsqueda» | Incorpora la actualización de Lecture 05 y comprueba que existe `data/rag_data/index.sqlite3`. Si configuraste `AIE_RAG_DB`, comprueba esa ruta |
| Se alcanza el límite de uso de la API | Espera según el mensaje y vuelve a ejecutar |
| La consulta está vacía | Si abriste otro terminal, define de nuevo `AIE_QUESTION` |
| Los resultados de búsqueda no responden a la pregunta | Prueba solo la búsqueda con `app.retrieval` y comprueba la consulta, los materiales seleccionados y el número de resultados |
| El modo de contexto completo supera el límite de entrada | Registra el error y las condiciones, y prueba otros métodos. Indica qué partes no pudiste ejecutar |

Los resultados pueden variar incluso con la misma pregunta. No decidas la superioridad de un método por un solo éxito o fallo; comprueba qué evidencias recuperó y utilizó.
