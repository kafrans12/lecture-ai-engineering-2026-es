# Lecture 05: respuestas

## Ejercicios

### 1. Pregunta, modelo y materiales

- **Modelo de respuesta (`[model]` al ejecutar):** `gemini-3.5-flash-lite`.
- **Pregunta comparada:** «¿Qué es un Agent Loop y cómo pueden acumularse los errores durante su ejecución?».
- **Materiales utilizados:** los métodos de búsqueda vectorial, Tree y Graph consultaron el índice RAG de las Lectures 01–03 (214 páginas: 73, 70 y 71, respectivamente). Full Context recibió un corpus más amplio, de **408.430 caracteres** en esta ejecución, por lo que los cuatro métodos no tuvieron exactamente el mismo alcance documental. El índice vectorial se almacenó localmente en `data/rag_data/index.sqlite3`.

La comparación principal se realizó **antes** de modificar la búsqueda vectorial. Todas las cifras de esta sección corresponden a la misma pregunta, ejecutada una vez por método. El costo informado es el estimado de la **API de generación**, sin incluir vectorización ni creación del índice.

### 2. Resultados por método

| Método | Resumen y corrección de la respuesta | Páginas citadas y evidencias | Tiempo (segundos) | Tokens de entrada/salida | Número de respuestas del modelo | Coste estimado de la API de generación (USD) |
|---|---|---|---:|---:|---:|---:|
| Contexto completo | Explicó el ciclo LLM → herramienta → LLM y la caída de probabilidad de éxito al encadenar pasos. Fue correcta, pero no desarrolló explícitamente las verificaciones intermedias. | Lecture 03, p. 12, 19 y 59; material de ejercicios de Lecture 03, p. 11. | 6,20 | 112.069 / 298 | 1 | 0,034366 |
| Búsqueda vectorial | Definió el Agent Loop y explicó tanto el ejemplo probabilístico como la falta de verificaciones intermedias. Respuesta correcta y bien fundamentada. | Lecture 03, p. 12, 19 y 20. | 5,66 | 6.274 / 300 | 3 | 0,002632 |
| Tree | Explicó el funcionamiento del loop y el ejemplo de 95 % de éxito por paso, con 36 % de éxito acumulado tras 20 pasos. Correcta, aunque no profundizó en los objetivos cuantitativos. | Lecture 03, p. 12 y 19. | 8,30 | 17.082 / 493 | 8 | 0,005818 |
| Graph | Explicó el loop, la acumulación probabilística y la necesidad de validaciones medibles por paso. Respuesta correcta y completa para esta pregunta. | Lecture 03, p. 19 y 20; la definición del loop también aparece en el texto de la respuesta. | 3,72 | 4.932 / 373 | 2 | 0,002412 |

**Interpretación:** los cuatro métodos contestaron adecuadamente la pregunta. Full Context tuvo el mayor consumo de tokens y costo; Tree realizó más interacciones; Graph fue el más rápido y económico **en esta única ejecución**. Esto no demuestra que Graph sea siempre superior.

### 3. Páginas encontradas al ejecutar solo la búsqueda y comprobación de evidencias

Antes de implementar Neighbor Expansion, ejecuté directamente `search("Agent Loop errores acumulados")`, sin agente. La búsqueda devolvió:

| Posición | Página | Distancia | Título |
|---|---|---:|---|
| 1 | `lec03-main-p018` | 0,2883 | Parte 3: Loop |
| 2 | `lec03-main-p019` | 0,2937 | Errores acumulados |
| 3 | `lec03-main-p048` | 0,3281 | Garantizar la idempotencia |
| 4 | `lec03-main-p020` | 0,3304 | La importancia de objetivos cuantitativos |
| 5 | `lec03-main-p021` | 0,3318 | autoresearch |

Después revisé el contenido original de tres páginas con `load_pages()`:

- **`lec03-main-p012` — «Loop: el resultado de la herramienta vuelve automáticamente al modelo».** Muestra la secuencia: el modelo escribe una llamada, el harness ejecuta la herramienta y el resultado vuelve al contexto. **Respalda la definición de Agent Loop**.
- **`lec03-main-p019` — «Errores acumulados».** Indica que, con un 95 % de éxito por paso y suponiendo independencia, completar 20 pasos consecutivos tiene una probabilidad aproximada del 36 % (`0,95^20 ≈ 0,3585`). **Respalda la explicación de acumulación probabilística**.
- **`lec03-main-p020` — «La importancia de objetivos cuantitativos».** Explica que los errores se acumulan sin verificación intermedia y propone condiciones medibles, como pasar pruebas y lint, alcanzar una puntuación de benchmark o tener cero errores de tipo. **Respalda la necesidad de validaciones para corregir el rumbo**.

La página `lec03-main-p048` (idempotencia) estaba relacionada con la confiabilidad de herramientas, pero no era una evidencia tan directa para esta pregunta. También es importante distinguir que **la página 12 fue consultada para comprobar la evidencia, aunque no apareció entre los cinco resultados de esa búsqueda aislada**; sí apareció en las referencias de respuestas del agente.

### 4. Llamadas a herramientas observadas con `--trace`

**Contexto completo:** no realizó llamadas a herramientas; el modelo recibió directamente 408.430 caracteres de material.

```text
[full-context] Entrada: 408,430 caracteres
[time] Respuesta completada en 6.20 segundos
[usage] Entrada: 112,069 tokens / Salida: 298 tokens / Respuestas del modelo: 1
[cost] Coste estimado de la API de generación: $0.034366 USD
```

**Búsqueda vectorial:** realizó dos llamadas a `search_materials`, orientadas primero a los errores y luego a la definición del loop.

```text
[tool call] search_materials({'query': 'Agent Loop errores'})
[tool call] search_materials({'query': 'Agent Loop definición pasos'})
[time] Respuesta completada en 5.66 segundos
[usage] Entrada: 6,274 tokens / Salida: 300 tokens / Respuestas del modelo: 3
[cost] Coste estimado de la API de generación: $0.002632 USD
```

**Tree:** recorrió el índice general, el documento Lecture 03, la sección «Parte 3: Loop» y páginas específicas. También consultó «Parte 2: Construir un agente» para recuperar la definición del ciclo.

```text
[tool call] browse_tree({})
[tool call] browse_tree({'node_id': 'lec03-main'})
[tool call] browse_tree({'node_id': 'lec03-main-s018'})
[tool call] browse_tree({'node_id': 'lec03-main-p018'})
[tool call] browse_tree({'node_id': 'lec03-main-p019'})
[tool call] browse_tree({'node_id': 'lec03-main-s005'})
[tool call] browse_tree({'node_id': 'lec03-main-p012'})
[time] Respuesta completada en 8.30 segundos
[usage] Entrada: 17,082 tokens / Salida: 493 tokens / Respuestas del modelo: 8
[cost] Coste estimado de la API de generación: $0.005818 USD
```

En la traza se observa que `lec03-main-p018` contenía solo 31 caracteres, mientras que `lec03-main-p019` devolvió 1.202 caracteres y `lec03-main-p012` devolvió 345. Esto muestra que recorrer un nodo o una página no garantiza recuperar una cantidad significativa de información útil.

**Graph:** realizó una llamada a `search_graph`, partiendo de resultados semánticos y sus relaciones en el grafo.

```text
[tool call] search_graph({'query': 'Agent Loop errors accumulation'})
[tool return] search_graph -> {"seeds": [{"page_id": "lec03-main-p018", ...}]}
[time] Respuesta completada en 3.72 segundos
[usage] Entrada: 4,932 tokens / Salida: 373 tokens / Respuestas del modelo: 2
[cost] Coste estimado de la API de generación: $0.002412 USD
```

Los fragmentos anteriores son extractos de las salidas registradas; se omiten los mensajes decorativos de la terminal y los cuerpos extensos de los resultados de herramientas.

### 5. Información insuficiente o recuperada que no se aprovechó

- **Resultado relacionado, pero poco específico:** la página `lec03-main-p048`, sobre idempotencia, apareció en la búsqueda vectorial aislada. Puede aportar contexto sobre seguridad de operaciones, pero no explica directamente la probabilidad acumulada ni las verificaciones cuantitativas solicitadas.
- **Página de navegación con escaso contenido:** Tree consultó `lec03-main-p018` («Parte 3: Loop»), cuyo texto recuperado fue de solo 31 caracteres. La página sirvió principalmente para orientarse hacia contenido sustantivo.
- **Evidencia no desarrollada en la respuesta:** Full Context disponía de muchos materiales y explicó el ejemplo probabilístico, pero no aprovechó explícitamente la explicación de objetivos cuantitativos de `lec03-main-p020`. Tree tampoco desarrolló ese aspecto en su respuesta final.

No se observó una respuesta completamente incorrecta en estas cuatro ejecuciones; las diferencias fueron de profundidad, selección de evidencias y eficiencia.

### 6. Método que adoptaría, motivos y limitaciones de la comparación

Adoptaría **búsqueda vectorial como punto de partida** para un asistente que responde preguntas sobre apuntes de clase: recupera páginas específicas, permite inspeccionar las evidencias y ofrece un comportamiento sencillo de modificar y probar. Graph también merece consideración, porque en esta pregunta proporcionó una respuesta completa con el menor costo y tiempo observados.

No elegiría un método únicamente por su velocidad: evaluaría primero la corrección de la respuesta, la pertinencia de las citas y el uso efectivo de las evidencias. La comparación tiene limitaciones: una sola ejecución por método, una única pregunta, un corpus más amplio en Full Context y costos que excluyen embeddings y construcción del índice. Por ello, los resultados no son una prueba estadística de superioridad.

### 7. Observaciones y dudas del ejercicio

La búsqueda selectiva puede reducir significativamente los tokens frente a enviar todo el material, pero recuperar una página relacionada no garantiza que sea la mejor evidencia. Tree hizo visible el recorrido documental; Vector y Graph fueron más directos para esta pregunta. Me interesa profundizar en cómo medir relevancia de evidencias, cómo evaluar respuestas de forma repetible y cuándo conviene combinar estrategias de recuperación.

---

## Tarea

### 1. Nivel elegido

**Implementación.**

### 2. Qué hice: Neighbor Expansion

Modifiqué `app/retrieval.py` para admitir `search(query: str, expand_neighbors: bool = False)`. La búsqueda original devuelve las páginas más similares; al activar la expansión se añaden, cuando existen, la página anterior y la posterior de cada resultado. El procedimiento elimina duplicados y respeta los límites de los documentos.

En `app/tools.py`, la herramienta `search_materials` utiliza la expansión. La búsqueda interna utilizada por Graph conserva la modalidad original sin expansión. Mantener `expand_neighbors=False` como valor predeterminado en `search()` permite comparar ambas estrategias y evitar que todos los consumidores de la función cambien de comportamiento.

Verifiqué que la funcionalidad llegaba realmente a la herramienta del agente, que no producía duplicados y que se comportaba correctamente en páginas iniciales y finales. Las pruebas automatizadas de `tests/test_build_rag_index.py` y `tests/test_agent.py` finalizaron con **4 pruebas aprobadas**.

### 3. Primera validación: misma pregunta de Agent Loop, antes y después

Para aislar el cambio, volví a ejecutar **la misma pregunta del ejercicio inicial** con el agente vectorial, ahora con Neighbor Expansion habilitado. No cambié el modelo ni el índice documental; las consultas que el agente decidió formular sí variaron entre ejecuciones.

| Indicador | Vector original | Vector con Neighbor Expansion |
|---|---:|---:|
| Tiempo | 5,66 s | 5,17 s |
| Tokens de entrada | 6.274 | 11.124 |
| Tokens de salida | 300 | 292 |
| Respuestas del modelo | 3 | 3 |
| Llamadas a herramientas | 2 | 2 |
| Costo estimado de generación | USD 0,002632 | USD 0,004067 |

**Traza después de la modificación:**

```text
[tool call] search_materials({'query': 'Agent Loop errores acumularse'})
[tool call] search_materials({'query': 'Agent Loop resultados de herramientas'})
[time] Respuesta completada en 5.17 segundos
[usage] Entrada: 11,124 tokens / Salida: 292 tokens / Respuestas del modelo: 3
[cost] Coste estimado de la API de generación: $0.004067 USD
```

La nueva respuesta explicó correctamente el ciclo modelo–herramienta–harness, el ejemplo de 95 % de éxito por paso y la necesidad de verificaciones intermedias. **No identifiqué una mejora conceptual clara** frente a la respuesta original, aunque sí aumentaron los tokens de entrada y el costo. La reducción puntual del tiempo no puede atribuirse con seguridad a la expansión a partir de una sola ejecución.

**Verificación directa de la herramienta:** al consultar `search_materials("Agent Loop errores acumulados")`, obtuve nueve páginas únicas:

```text
lec03-main-p018
lec03-main-p017
lec03-main-p019
lec03-main-p020
lec03-main-p048
lec03-main-p047
lec03-main-p049
lec03-main-p021
lec03-main-p022
Sin duplicados: True
```

Esto confirmó que las páginas vecinas llegaban al agente y que la expansión no repetía identificadores.

### 4. Pruebas adicionales: por qué construí un benchmark

La primera comparación mostró que Neighbor Expansion funcionaba, pero no bastaba para saber si realmente mejoraba la recuperación o las respuestas. Por eso amplié la evaluación a **seis preguntas de distintos temas** y separé dos problemas: **qué páginas recuperamos** y **qué respuesta genera el modelo con ellas**.

El objetivo fue conservar las condiciones de cada caso, guardar las evidencias y no depender de que la terminal permaneciera abierta.

### 5. Diseño, archivos y persistencia del benchmark

Para que la comparación no dependiera de capturas de pantalla o de mantener abierta la terminal, construí un benchmark incremental en `benchmarks/lecture05/`. Separé la **definición de casos**, la **recuperación de páginas**, la **generación de respuestas** y los **resultados persistidos**.

```text
benchmarks/lecture05/
├── cases.json
├── run_benchmark.py
├── run_generation_benchmark.py
└── results/
    ├── <slug>_baseline.json                 (6 archivos)
    ├── <slug>_neighbors.json                (6 archivos)
    ├── memoria_baseline_generation.json
    ├── memoria_neighbors_generation.json
    ├── structured_output_baseline_generation.json
    └── structured_output_neighbors_generation.json
```

Los nombres con `<slug>` representan los seis identificadores de `cases.json`: `structured_output`, `prompt_injection`, `idempotencia`, `lora_qlora`, `tokenizacion` y `memoria`. En total, el registro de nuestras ejecuciones corresponde a **12 resultados de recuperación y 4 de generación**. Los archivos son artefactos de evidencia, no un índice vectorial nuevo.

| Archivo | Función concreta | Datos relevantes |
|---|---|---|
| `cases.json` | Define las seis preguntas y las páginas candidatas para cada una. | `id`, `slug`, `question`, `candidate_page_ids`, `relevance_reviewed: false`. |
| `run_benchmark.py` | Ejecuta `search(question, expand_neighbors=False)` y `search(question, expand_neighbors=True)` por caso. | Variante, IDs, páginas únicas, caracteres, páginas candidatas encontradas, resultados completos y fecha UTC. |
| `run_generation_benchmark.py` | Lee los JSON de recuperación y envía sus páginas como contexto fijo a `gemini-3.5-flash-lite`, mediante Google GenAI. **No vuelve a buscar ni ejecuta el Agent Loop.** | Respuesta, IDs citables, fuente del contexto, modelo, fecha UTC y metadatos de tokens. |
| `results/` | Conserva un JSON por caso y variante. | Permite auditar cada comparación y reutilizar los contextos sin repetir llamadas de recuperación. |

**Persistencia y recuperación ante interrupciones.** Los scripts guardan **cada variante inmediatamente** después de ejecutarla. Escriben primero un archivo temporal `.tmp`, fuerzan la escritura al disco y reemplazan el archivo definitivo (`os.replace`), para reducir el riesgo de un JSON incompleto. Si el archivo de resultado ya existe, lo omiten al reanudar; `--force` permite sobrescribirlo voluntariamente. Esto fue especialmente importante después de perder salidas cuando se cerró VS Code.

**Ejecución desde la raíz del repositorio:**

```powershell
python benchmarks/lecture05/run_benchmark.py --case 1
python benchmarks/lecture05/run_benchmark.py --case 2
python benchmarks/lecture05/run_benchmark.py --case 3
python benchmarks/lecture05/run_benchmark.py --case 4
python benchmarks/lecture05/run_benchmark.py --case 5
python benchmarks/lecture05/run_benchmark.py --case 6
python benchmarks/lecture05/run_generation_benchmark.py --case memoria
python benchmarks/lecture05/run_generation_benchmark.py --case structured_output
```

Estos comandos documentan el procedimiento; **no es necesario volver a ejecutarlos** para interpretar los resultados que ya guardamos.

**Relación con las pruebas automatizadas.** `tests/test_build_rag_index.py` y `tests/test_agent.py` comprobaron la regresión técnica (**4 pruebas aprobadas**). En cambio, los scripts de benchmark evalúan el comportamiento de la recuperación y las respuestas con preguntas concretas. Aprobar las pruebas automatizadas no demuestra por sí solo una mejora en la calidad de las respuestas.

### 6. Preguntas exactas y condiciones del benchmark

Las siguientes preguntas y páginas candidatas provienen de `cases.json`:

| Caso | Pregunta utilizada | Páginas candidatas |
|---|---|---|
| Structured Output | ¿En qué se diferencian Structured Output y Constrained Decoding, y cómo garantizan un formato JSON válido? | `lec03-main-p034`, `lec03-main-p035` |
| Prompt Injection | ¿Por qué una instrucción maliciosa dentro de un archivo puede comprometer a un agente y cómo ayudan los límites de confianza? | `lec03-main-p050`, `lec03-main-p051` |
| Idempotencia | ¿Por qué es importante la idempotencia cuando un agente ejecuta herramientas o reintenta operaciones? | `lec03-main-p027`, `lec03-main-p048` |
| LoRA / QLoRA | ¿Qué diferencias existen entre LoRA y QLoRA para ajustar modelos grandes? | `lec02-main-p051`, `lec02-main-p052` |
| Tokenización | ¿Qué es la tokenización y cómo se relaciona con la generación de tokens de un LLM? | `lec02-main-p009`, `lec02-main-p010` |
| Memoria | ¿Por qué necesitan memoria los agentes y cómo pueden conservar información entre sesiones? | `lec03-main-p038`, `lec03-main-p039`, `lec03-main-p040` |

**Condiciones controladas en recuperación:** misma pregunta, mismo índice y configuración de embeddings; se modificó únicamente el valor de `expand_neighbors`. El script registró las páginas completas de cada variante, no solo sus identificadores.

**Condiciones controladas en generación:** se eligieron los casos **memoria** y **Structured Output**; se mantuvieron la pregunta, el modelo y las instrucciones de respuesta de cada caso. Cambió el conjunto de páginas previamente recuperadas. Se pidió responder solo con el material proporcionado, citar IDs de página exactos y reconocer insuficiencia de evidencia. Por ello, esta fase mide generación con contexto fijo y **no equivale** a repetir la ejecución interactiva del agente.

**Precaución sobre las referencias:** `cases.json` marca `reference_status: candidate_unverified_relevance` y `relevance_reviewed: false`. Las páginas candidatas son una comprobación inicial, no una anotación exhaustiva de relevancia. Por tanto, la proporción encontrada **no es recall ni precision formal**.

### 7. Resultados adicionales: recuperación

| Caso | Páginas sin expansión | Páginas con expansión | Referencias candidatas encontradas |
|---|---:|---:|---|
| Structured Output | 5 | 9 | 2/2 en ambas |
| Prompt Injection | 5 | 7 | 2/2 en ambas |
| Idempotencia | 5 | 11 | 2/2 en ambas |
| LoRA / QLoRA | 5 | 11 | 2/2 en ambas |
| Tokenización | 5 | 10 | 2/2 en ambas |
| Memoria | 5 | 11 | 3/3 en ambas |
| **Total** | **30** | **59** | **13/13 en ambas** |

En conjunto, la búsqueda original recuperó **28.060 caracteres** y Neighbor Expansion **51.538 caracteres**, un incremento del **83,7 %**. Las dos estrategias encontraron las mismas 13 referencias candidatas. Por tanto, **en estos casos no se observó una mejora en la cobertura de esas referencias**, aunque sí aumentó el contexto disponible.

Las referencias candidatas **no constituyen un conjunto exhaustivo de relevancia**. El indicador 13/13 no debe presentarse como una medición formal de *recall* o *precision*.

### 8. Resultados adicionales: generación con contexto guardado

| Caso | Variante | Páginas | Tokens de entrada | Tokens de salida | Tokens totales |
|---|---|---:|---:|---:|---:|
| Memoria | Original | 5 | 1.328 | 336 | 1.664 |
| Memoria | Neighbor Expansion | 11 | 2.662 | 526 | 3.188 |
| Structured Output | Original | 5 | 1.318 | 159 | 1.477 |
| Structured Output | Neighbor Expansion | 9 | 2.363 | 135 | 2.498 |
| **Total** | **Original** | | **2.646** | **495** | **3.141** |
| **Total** | **Neighbor Expansion** | | **5.025** | **661** | **5.686** |

La expansión incrementó un **81,0 % los tokens totales** de estas dos comparaciones.

- **Memoria:** ambas variantes produjeron explicaciones coherentes; la expandida fue más extensa, sin una mejora conceptual claramente identificable.
- **Structured Output:** la variante original explicó la relación entre el esquema JSON y Constrained Decoding. La variante expandida afirmó no contar con información suficiente para desarrollar adecuadamente la distinción, pese a que se habían recuperado páginas relevantes. En esta ejecución, **más contexto produjo una respuesta menos útil**.

El script generativo guarda `usage` (tokens) y el texto de la respuesta, pero no mide un tiempo comparable ni calcula el costo de API por variante; por eso no asigno valores estimados no medidos. Los valores de tiempo y costo de la ejecución completa del agente están en la sección 3 de esta tarea.

### 9. Inspección cualitativa de páginas adicionales

Además de contar páginas, inspeccioné qué aportaban algunas de las páginas vecinas recuperadas. Esta revisión ayuda a explicar por qué el aumento de contexto no equivale automáticamente a una mejora de respuesta:

| Caso | Ejemplos de páginas añadidas | Interpretación de su utilidad |
|---|---|---|
| Idempotencia | `lec03-main-p026` (HITL), `p028` (fuga de datos), `p047` (trampas del prompt), `p049` (límites de confianza), `p031` (subagentes), `p024` (permisos MCP). | Aportan contexto de seguridad y herramientas, pero varias son periféricas a la definición de idempotencia. |
| LoRA / QLoRA | `lec02-main-p053` (fine-tuning de chatbots), `p050` (decisiones de ajuste), `p059` (resumen), `p046` (comportamiento de fine-tuning), `p048` (CPT), `p062` (agentes). | Algunas amplían el tema de fine-tuning; otras se alejan de la comparación concreta LoRA/QLoRA. |
| Memoria | `lec03-main-p012` (loop), `p014` (harness), `p037` (introducción a memoria), `p041` (skills frente a memoria), `p064` (tareas largas), `p066` (skills). | Pueden ampliar el contexto de agentes, pero la respuesta expandida no aprovechó claramente todas esas relaciones. |
| Prompt Injection | `lec03-main-p054` (RSI), `p048` (idempotencia). | Relación indirecta con el tema principal. |
| Structured Output | `lec03-main-p061` (SDK), `p063` (tool calls), `p037` (memoria), `p032` (tool search). | Varias páginas no explican directamente la diferencia entre Structured Output y Constrained Decoding. |
| Tokenización | `lec02-main-p007` (probabilidad), `p011` (parámetros), `p005` (panorama), `p014` (respuestas plausibles), `p016` (quiz). | Contexto general sobre LLM, pero no necesariamente evidencia específica sobre tokenización. |

Esta valoración fue una **inspección cualitativa preliminar**, no una clasificación formal página por página. La evidencia más clara de un resultado adverso fue el caso Structured Output: con más páginas disponibles, el modelo produjo una respuesta menos informativa que con la búsqueda original.

### 10. Mejoras, fallos y limitaciones que persisten

**Mejoras verificadas:** la funcionalidad añade páginas adyacentes, evita duplicados, respeta los límites de los documentos, conserva el comportamiento original como opción y está integrada en la herramienta del agente. Los scripts y archivos JSON permiten repetir y auditar la comparación.

**Limitaciones observadas:** las páginas vecinas pueden ser irrelevantes, aumentar el costo o distraer al modelo; en los seis casos no mejoraron la cobertura de referencias candidatas; en Structured Output se obtuvo una respuesta generativa menos útil. Las pruebas generativas se ejecutaron una vez por variante y caso, por lo que existe variabilidad no medida y no puede afirmarse una relación causal definitiva.

### 11. Observaciones y dudas de la tarea

Esta implementación me permitió distinguir entre **recuperar más contenido** y **recuperar evidencia que mejora la respuesta**. Neighbor Expansion funciona técnicamente, pero los datos no justifican activarla indiscriminadamente. La conservaría como una opción configurable y evaluaría una expansión selectiva basada en relevancia, un mecanismo de *reranking* o una segunda búsqueda solo cuando la evidencia inicial sea insuficiente.

Como trabajo futuro, ampliaría los casos, repetiría las ejecuciones y definiría criterios de evaluación de relevancia por página y corrección de respuestas. Desde una perspectiva de QA, el aprendizaje más importante fue convertir un cambio de código en un experimento **trazable, verificable y con limitaciones explícitas**.
