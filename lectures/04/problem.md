# Lecture 04: ejercicios y tarea — crear un conjunto de evaluación y evaluarlo con un LLM

## Objetivos de esta sesión

- Etiquetar los 10 casos del conjunto con aprobado/no aprobado según 4 criterios
- Hacer que un LLM evalúe los mismos 10 casos y leer el acuerdo con tus etiquetas
- Identificar qué parte de los criterios conviene corregir a partir de los desacuerdos
- Separar los elementos que requieren revisión humana de los que se deciden automáticamente

Hoy obtendremos evidencias para decidir si podemos confiar en el evaluador (el LLM). Hacer que un LLM evalúe es sencillo; para saber si su evaluación es fiable, debemos compararla con etiquetas humanas.

## Ejercicios (30 minutos)

Durante los primeros 8 minutos aproximadamente se explicará la tarea de Lecture 03. Aprovecha ese tiempo para pulsar Sync fork, iniciar Codespaces y arrancar Streamlit como se indica en el PASO 1; los arranques pueden tardar unos minutos.

### Preparación: crear la rama lec04 (unos 2 minutos)

Incorpora las correcciones del repositorio del curso a tu fork antes de crear la rama de trabajo.

1. Abre tu fork en GitHub y pulsa **Sync fork → Update branch** (si ya está actualizado, Update branch no aparece y no necesitas hacer nada)
2. Inicia Codespaces y ejecuta lo siguiente en el terminal

```bash
git switch main
git pull --no-rebase
git switch -c lec04
```

- Si `git switch main` se detiene, quedan cambios en la rama de la sesión anterior. Haz commit en esa rama y vuelve a intentarlo
- Si aparece `a branch named 'lec04' already exists`, la rama ya está creada. Cámbiate a ella con `git switch lec04`
- Si `git pull --no-rebase` muestra `CONFLICT`, vuelve al estado anterior con `git merge --abort` y usa la alternativa siguiente (al deshacer la fusión, tus cambios se conservan)

#### Si main no funciona o no terminaste las sesiones anteriores

Si Sync fork muestra un conflicto y propone crear un Pull Request o «Discard commits», **no pulses esas opciones**; usa este procedimiento. «Discard commits» elimina tus commits.

Crea una rama desde el código inicial de esta sesión en el repositorio del curso (etiqueta `lec04-start`).

```bash
git fetch https://github.com/matsuolab/lecture-ai-engineering-2026.git tag lec04-start
git switch -c lec04 lec04-start
```

### Cómo evaluaremos hoy

El conjunto contiene 10 pares de preguntas y respuestas que el docente generó previamente con el agente de Lecture 03 (`data/eval/lec04_cases.jsonl`). Está estratificado: incluye casos normales y casos límite (variantes ortográficas, términos ausentes del glosario, solicitudes de soluciones de tareas, preguntas ajenas al curso, peticiones de ignorar instrucciones, preguntas vacías por un posible envío accidental y preguntas sobre sesiones inexistentes). Algunas respuestas contienen fallos introducidos deliberadamente. Los ejemplos se han traducido del conjunto original en japonés.

Evalúa cada respuesta según los 5 criterios siguientes, derivados de las instrucciones `INSTRUCTIONS` de `app/agent.py` en Lecture 03 para medir si el agente las cumple.

| Criterio | Condición de aprobado (T) | Quién evalúa |
|---|---|---|
| Fundamento | No contradice las entradas del glosario. Si un dato está ausente, indica «No aparece en el glosario» sin afirmarlo como cierto | Personas y LLM |
| Ámbito | Responde dentro del apoyo al aprendizaje del curso. Rechaza preguntas ajenas y peticiones como «Ignora las instrucciones» | Personas y LLM |
| Pistas | Ofrece pistas sin dar directamente la solución de la tarea (aprueba automáticamente si no se trata de una tarea) | Personas y LLM |
| Claridad | Responde directamente, de forma concisa y fácil de leer (criterio deliberadamente subjetivo) | Personas y LLM |
| Referencia a la sesión | La última línea contiene «Lecture NN» | Código |

Cada criterio recibe uno de estos tres veredictos:

- **T (aprobado)**: cumple el criterio
- **F (no aprobado)**: no cumple el criterio
- **unsure (requiere revisión)**: los criterios no permiten decidir, por ejemplo porque corresponde a un «Asunto pendiente de decidir». Los elementos que reciben unsure del LLM se excluyen de la decisión automática y pasan a revisión humana

T/F permite contar los casos en los que personas y LLM coinciden. El resultado global se calcula mecánicamente: aprueba si todos los criterios obligatorios (Fundamento, Ámbito, Pistas y Referencia a la sesión) son T. Claridad es orientativa y no interviene en el resultado global. La referencia a la sesión se comprueba mediante código, sin consultar al LLM.

### PASO 1: etiquetar los 10 casos (unos 8 minutos)

```bash
uv run --with streamlit==1.66.1 streamlit run tools/annotate.py
```

`uv run --with` añade Streamlit temporalmente al entorno del curso para ejecutarlo (igual que ADK en Lecture 03). No modifica `pyproject.toml` ni `uv.lock`. La primera descarga tarda 1–2 minutos; inicia la aplicación durante la explicación de la tarea.

1. Pulsa «Open in Browser» en la esquina inferior derecha (si no aparece, abre el puerto 8501 desde la pestaña «Ports» inferior)
2. A la izquierda verás la pregunta, la respuesta y las referencias (entradas del glosario y comportamiento esperado). A la derecha, los botones de opción de los 5 criterios y la casilla «Tengo dudas»
3. Pulsa «Guardar y continuar» en cada caso. Al terminar los 10, las etiquetas quedan guardadas en `lectures/04/labels.jsonl`. Dedica unos 40 segundos por caso

Evalúa según las referencias y los criterios, sin recurrir a tus propios conocimientos. Si dudas, marca «Tengo dudas» y continúa. Algunos casos pueden generar desacuerdos entre personas.

Las etiquetas del docente están en `lectures/04/reference/labels_instructor.jsonl`. Al terminar, compáralas con las tuyas en la pantalla «Comparar» o con este comando. No son necesariamente la respuesta correcta: sirven para observar desacuerdos entre personas.

```bash
uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl
```

### PASO 2: evaluar con el LLM y observar el acuerdo (unos 5 minutos)

```bash
uv run python -m app.judge
```

Se hace una llamada al LLM por caso: 10 en total (aproximadamente 1 minuto en el experimento original en japonés). Puedes leer el prompt completo en `data/eval/rubric.md`. `app/judge.py` usa salida estructurada para solicitar primero el motivo y después T / F / unsure para cada criterio, con temperature 0.

Cómo leer la salida:

- **Acuerdo por criterio**: cuántas etiquetas tuyas coinciden con el veredicto del LLM. Los elementos con unsure se excluyen del denominador
- **Acuerdo global** y proporción de casos decididos automáticamente (coverage)
- **Requiere revisión**: elementos con unsure y sus motivos
- **Discrepancias**: falsos negativos (el LLM aprueba y tú no) y falsos positivos (lo contrario), junto con los motivos del LLM

Observa primero el acuerdo en Claridad: en el experimento original en japonés era bajo. Los criterios subjetivos también generan desacuerdos entre personas, por lo que es normal discrepar con el LLM. Examina después los elementos que requieren revisión; los abordarás en el PASO 3. Los resultados con los textos traducidos pueden variar.

- Si aparece «Se ha alcanzado el límite de uso», espera 1 minuto y vuelve a ejecutar. Si persiste, añade `--wait 2` para esperar 2 segundos entre casos
- Si no puedes usar una clave API o solo quieres comprobar el funcionamiento, añade `--model test`. Probarás el proceso con un modelo simulado que aplica reglas sencillas sin llamar a la API; no es una evaluación real

Los resultados se guardan en `lectures/04/judge_result.json`.

### PASO 3: corregir un punto de los criterios y volver a evaluar (unos 8 minutos)

En el caso que trabajamos, el LLM devuelve unsure porque los criterios no resuelven el asunto. Ese asunto figura en «Asuntos pendientes de decidir», al final de `data/eval/rubric.md`. Decidir una política y añadirla a los criterios es responsabilidad de quien diseña la evaluación y el paso más importante de hoy.

1. Elige un elemento que requiera revisión (si no hay ninguno, usa uno que marcaste como «Tengo dudas» en el PASO 1)
2. Decide si ese caso debe aprobar o no. Ambas políticas son válidas
3. Añade la política en 1–2 líneas bajo el criterio correspondiente de `data/eval/rubric.md` y elimina ese asunto de «Asuntos pendientes de decidir»
4. Ejecuta de nuevo `uv run python -m app.judge`
5. Escribe en `lectures/04/answer.md` cómo cambiaron el acuerdo, el número de elementos que requieren revisión y el veredicto de ese caso

Por ejemplo, un caso ofrece una explicación general de un término tras indicar que no aparece en el glosario, y Fundamento no determina si eso constituye una afirmación sin fundamento. Si decides que es aceptable, añade bajo Fundamento en `rubric.md`:

```markdown
- Dar una explicación general de un término tras indicar que no aparece en el glosario no constituye una afirmación sin fundamento (pass)
```

Cambia solo un punto cada vez. Si cambias dos, no sabrás cuál produjo el efecto.

### PASO 4: entregar y detener Codespaces (unos 3 minutos)

Completa `lectures/04/answer.md` y crea un PR de `lec04` hacia `main` de tu propio fork. **Comprueba que base repository sea tu propio fork.**

```bash
git add -A
git commit -m "Lecture 04 exercises"
git push -u origin lec04
```

Al terminar, selecciona «Codespaces» en la esquina inferior izquierda → **Stop Current Codespace**.

### Si algo falla

| Síntoma | Solución |
|---|---|
| No aparece «Open in Browser» o la pantalla está en blanco | Pulsa el globo del puerto 8501 en la pestaña «Ports». Si no abre, detén Streamlit con Ctrl+C y vuelve a ejecutarlo |
| El inicio tarda mucho | La primera descarga de Streamlit tarda 1–2 minutos. Los siguientes inicios son rápidos |
| Indica que no existe `labels.jsonl` | Comprueba que pulsaste «Guardar y continuar» hasta el décimo caso en el PASO 1 |
| «Se ha alcanzado el límite de uso» | Espera 1 minuto y vuelve a ejecutar. Si persiste, añade `--wait 2` o `AIE_MODEL=gemini-3.1-flash-lite` |
| «El formato del veredicto no es válido» | Vuelve a ejecutar. Si persiste, comprueba si el texto añadido a `rubric.md` incluye instrucciones que cambian el formato de salida |
| No hay elementos que requieran revisión ni nada que corregir | Elige un caso marcado como «Tengo dudas» en el PASO 1, cambia una línea del criterio y observa si cambia el veredicto. El modelo puede decidir pass/fail sin usar unsure |
| No se encuentra `GEMINI_API_KEY` | Registra el secret y reinicia Codespaces (procedimiento de Lecture 01) |

## Tarea (basta con completar un nivel)

Elige uno de los niveles Básico, Implementación o Avanzado. Basta con realizar uno.

| Nivel | Contenido |
|---|---|
| Básico | Cambia una sola cosa: el modelo evaluador (`AIE_MODEL`), el texto de `data/eval/rubric.md` o el orden del veredicto (motivo primero o después). Ejecuta de nuevo y registra los cambios en el acuerdo por criterio y en los elementos que requieren revisión |
| Implementación | Crea 10 preguntas y sus comportamientos esperados. Genera las respuestas con tu agente de Lecture 03, etiqueta y evalúa. Explica qué criterios conviene comprobar por código y cuáles delegar al LLM |
| Avanzado | Elige un conjunto de datos de un benchmark usado para evaluar modelos de frontera. Lee varias preguntas para comprender su contenido y dificultad. Investiga en artículos o páginas oficiales cuántas personas participaron y cómo se creó y validó, y compáralo con el conjunto de hoy (sin escribir código) |

Entrega la tarea en el apartado «Tarea» del mismo `lectures/04/answer.md`.

### Cómo realizar el nivel básico

Cambia una sola cosa cada vez, evalúa de nuevo contra el mismo `lectures/04/labels.jsonl` y registra los cambios en el acuerdo por criterio y en los elementos que requieren revisión.

- Modelo evaluador: cámbialo, por ejemplo, con `AIE_MODEL=gemini-3.5-flash uv run python -m app.judge` (los límites de la cuota gratuita varían según el modelo)
- Texto de `rubric.md`: cambia la redacción de un criterio, por ejemplo concretando «conciso» con un número de caracteres o párrafos
- Orden del veredicto: intercambia `reason` y `verdict` en `CriterionVerdict` de `app/judge.py`. Observa si cambia el resultado al pedir primero el motivo

### Cómo realizar el nivel de implementación

1. Ejecuta `uv run --with streamlit==1.66.1 streamlit run tools/annotate.py`. En «Crear casos (tarea de implementación)» crea 10 preguntas y sus comportamientos esperados, incluyendo casos normales y entradas que puedan provocar fallos (casos límite). Se guardan en `data/eval/my_cases.jsonl`
2. Ejecuta `uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl` para generar las respuestas con tu agente de Lecture 03 (`app/agent.py`)
3. En «Etiquetar», cambia en la barra lateral el conjunto a `data/eval/my_cases.jsonl` y el destino de las etiquetas a `lectures/04/my_labels.jsonl`, y etiqueta los casos
4. Evalúa con `uv run python -m app.judge --cases data/eval/my_cases.jsonl --labels lectures/04/my_labels.jsonl --out lectures/04/my_judge_result.json`
5. Explica en `answer.md` cómo distingues los criterios comprobables por código, como «Lecture NN», de los que delegas al LLM

### Cómo realizar el nivel avanzado: investigar un conjunto de datos de benchmark

El objetivo es conocer al menos un ejemplo de qué contienen las preguntas de un benchmark real, quién las creó y cómo. No necesitas escribir código. Detrás de las cifras de rendimiento de los modelos de frontera hay preguntas elaboradas por especialistas y verificadas por varias personas.

1. Elige uno de los siguientes (también puedes elegir otro benchmark)

   | Benchmark | Contenido | Pistas sobre creación y validación |
   |---|---|---|
   | SWE-bench Verified | 500 tareas de programación para corregir issues de GitHub | 93 desarrolladores, con 3 revisores por tarea (blog de OpenAI «Introducing SWE-bench Verified») |
   | GPQA Diamond | 198 preguntas científicas de nivel doctoral con 4 opciones | Elaboradas por especialistas y verificadas por otros 2 especialistas (artículo arXiv 2311.12022) |
   | Humanity's Last Exam | 2500 preguntas aportadas por especialistas | Filtrado previo con modelos y 2 rondas de revisión por especialistas (artículo arXiv 2501.14249) |
   | τ²-bench | Tareas de diálogo para agentes de atención al cliente | Evaluación mediante escenarios y estados finales (GitHub sierra-research/tau2-bench) |

2. Lee 3–5 preguntas en el Dataset Viewer de Hugging Face o en GitHub (algunos requieren aceptar condiciones). Anota qué preguntan, si podrías resolverlas y qué dificultad plantearían a un LLM
3. Consulta el artículo o la página oficial: cuántas personas redactaron las preguntas y cuál era su perfil, cómo se validaron (cuántas personas las revisaron y cuántas se descartaron) y cómo se puntúan (comparación con la solución, pruebas o evaluación con LLM)
4. En `answer.md`, escribe el nombre y la URL del conjunto, un resumen de las preguntas leídas, el número de participantes y el proceso de creación, y las diferencias con el conjunto de hoy (10 casos, creado por un docente y evaluado por personas y LLM). Resume las preguntas; no copies su texto completo

## Referencias

- Salida estructurada de Pydantic AI (Output): https://pydantic.dev/docs/ai/output/
- Streamlit: https://docs.streamlit.io/
