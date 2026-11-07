# Lecture 03: respuestas

## Ejercicios

### Diferencias entre la respuesta de Lecture 01 (LLM sin herramientas) y la del agente

Para comparar ambos enfoques, realicé pruebas con `app.ask` (Lecture 01) y `app.agent` (Lecture 03), utilizando el modelo `gemini-3.5-flash-lite`.

**Primera comparación: concepto de agente de IA**

Ejecuté en ambos programas la pregunta: «¿Qué es un agente de IA y cómo funciona su ciclo de ejecución?».

El LLM sin herramientas generó una explicación extensa sobre percepción, razonamiento, planificación, ejecución de acciones y observación. También presentó un ejemplo práctico de búsqueda de inmuebles.

El agente de Lecture 03 respondió de manera más breve y enfocada en el curso. Antes de responder, consultó `search_glossary` con el argumento `{'query': 'Agente de IA'}`. Además, formuló una pregunta orientadora sobre el comportamiento del agente cuando una herramienta devuelve un error.

Ambas respuestas fueron conceptualmente adecuadas. La diferencia principal fue que el agente consultó una fuente específica y permitió verificar esa consulta mediante la traza.

**Segunda comparación: los tres niveles de tareas de AIE2026**

Retomé una dificultad que había identificado en Lecture 01: al preguntar por los niveles de tareas del curso, el LLM generaba clasificaciones generales que no coincidían con el glosario. Cambiar la temperatura y el modelo no había solucionado consistentemente esa falta de información específica.

En Lecture 03 pregunté: «¿Cuáles son los tres niveles de las tareas del curso AIE2026, qué se hace en cada nivel y es obligatorio completar los tres?».

El agente ejecutó `search_glossary` con `{'query': 'tareas'}` y respondió correctamente:

- **Básico:** repasar el contenido visto en clase.
- **Implementación:** escribir código propio.
- **Avanzado:** investigar y experimentar.

También aclaró que basta completar uno de los niveles y que, en principio, las tareas no se califican. La respuesta identificó correctamente que la información correspondía a Lecture 01.

Este resultado permitió comprobar que recuperar información del glosario puede mejorar la precisión en preguntas específicas del curso. No significa que un agente esté libre de errores, sino que dispone de una fuente adicional para fundamentar sus respuestas.

### Llamadas a herramientas observadas con `--trace`

**1. Consulta de un concepto**

`search_glossary({'query': 'Agente de IA'})`

La herramienta devolvió el concepto correspondiente a Lecture 03. La traza mostró `requests=2` y `tool_calls=1`.

**2. Consulta sobre las tareas**

`search_glossary({'query': 'tareas'})`

La herramienta recuperó la entrada «3 niveles de las tareas», correspondiente a Lecture 01. La traza mostró `requests=2` y `tool_calls=1`.

**3. Generación de un quiz**

`make_quiz({'lecture': 3})`

La herramienta generó la pregunta «¿Qué significa Agente de IA?». El agente presentó una sola pregunta sin revelar su respuesta al estudiante. La traza mostró `requests=2` y `tool_calls=1`.

**4. Registro de aprendizaje**

`save_learning_log(topic='Lecture 03 - Quiz Agente de IA', notes='...')`

La herramienta solicitó aprobación humana antes de guardar. Después de responder `s`, se ejecutó y confirmó la escritura en `learning_log/learning_log.md`.

También se probó el rechazo de una solicitud de guardado. Al responder `n`, la herramienta recibió una denegación y posteriormente se verificó que el contenido rechazado no se había añadido al archivo.

### Número de llamadas al LLM para una pregunta (`requests`)

En las pruebas realizadas con el agente:

| Escenario | requests | tool_calls |
|---|---:|---:|
| Explicación de agente de IA | 2 | 1 |
| Consulta de niveles de AIE2026 | 2 | 1 |
| Generación del quiz de Lecture 03 | 2 | 1 |

Estos resultados corresponden a las trazas de cada ejecución. El flujo de consulta mediante herramientas requiere que el modelo determine la llamada y posteriormente procese su resultado.

### Herramienta añadida y descripción de su docstring

Implementé `make_quiz(lecture: int) -> str`, que genera una pregunta a partir de los conceptos del glosario asociados a la sesión indicada.

También desarrollé `save_learning_log(topic: str, notes: str) -> str`, cuya documentación explica:

> Guarda un registro de aprendizaje en un archivo Markdown. Úsala cuando el estudiante solicite explícitamente guardar sus apuntes o registrar lo aprendido sobre un tema. Esta operación modifica archivos y requiere aprobación humana.

## Tarea

### Nivel elegido: Implementación

### Qué hice

Implementé y registré `make_quiz` para generar preguntas a partir del glosario del curso. También ajusté las instrucciones del agente para presentar una pregunta a la vez, ofrecer pistas progresivas, evaluar respuestas y evitar revelar anticipadamente las soluciones.

Como parte del ejercicio de implementación, añadí `save_learning_log`, una herramienta que permite almacenar apuntes en un archivo Markdown. La registré mediante `requires_approval=True` para que la escritura requiera autorización humana.

Incorporé `DeferredToolRequests` y `DeferredToolResults` para gestionar las aprobaciones y reanudar la ejecución del agente después de recibir la decisión del usuario.

Durante las pruebas identifiqué que el modelo podía volver a solicitar autorización después de un rechazo. Para mejorar este comportamiento, implementé un mecanismo que registra temporalmente las herramientas rechazadas durante la ejecución actual.

Inicialmente, el control comparaba el nombre de la herramienta y sus argumentos. Posteriormente lo modifiqué para bloquear cualquier nuevo intento de la misma herramienta durante esa ejecución, incluso cuando el agente cambia los argumentos.

También separé la lógica de autorización en `process_approvals()` para facilitar las pruebas automatizadas.

### Resultados

**1. Generación del quiz**

El agente utilizó `make_quiz(lecture=3)` para generar la pregunta «¿Qué significa Agente de IA?».

Respondí con mi propia definición y recibí retroalimentación. Identifiqué que debía explicar con mayor precisión el bucle iterativo de ejecución, el uso de herramientas y las condiciones de finalización.

**2. Prueba positiva de HITL**

Solicité guardar la pregunta, mi respuesta y los aprendizajes obtenidos.

El agente mostró los argumentos de `save_learning_log` y solicitó aprobación. Respondí `s`, la herramienta ejecutó la escritura y confirmó el resultado.

Al consultar el archivo Markdown, comprobé que el nuevo registro se había agregado sin sobrescribir el contenido anterior.

**3. Prueba negativa de HITL**

Solicité guardar unos apuntes y respondí `n` cuando apareció la autorización.

La traza indicó que la llamada fue rechazada. Después revisé el archivo y confirmé que los apuntes rechazados no habían sido agregados.

**4. Pruebas automatizadas de reintentos**

Implementé pruebas en `tests/test_hitl.py` para comprobar el rechazo de solicitudes repetidas.

Validé que, después de rechazar una herramienta, las nuevas solicitudes de esa misma herramienta se rechazan automáticamente durante la ejecución, aunque cambien su identificador o sus argumentos.

La lógica se probó de manera aislada, sin realizar llamadas al modelo ni escribir archivos reales.

**5. Pruebas de regresión**

Ejecuté `uv run pytest -q` y las pruebas finalizaron satisfactoriamente después de incorporar los cambios.

**6. Comparación con Lecture 01**

La consulta sobre los tres niveles de AIE2026 permitió observar una mejora concreta respecto de las pruebas originales del LLM sin herramientas.

El agente consultó el glosario y recuperó las definiciones correctas, evitando las clasificaciones generales incorrectas observadas anteriormente.

### Observaciones y limitaciones

- El CLI conserva el contexto de autorización durante una ejecución, pero no mantiene automáticamente una conversación entre comandos independientes.
- El bloqueo de una herramienta rechazada desaparece al finalizar el programa, por lo que una nueva ejecución permite solicitar autorización nuevamente.
- Las pruebas unitarias comprueban la lógica de bloqueo, pero no simulan todos los comportamientos posibles de un modelo generativo.
- El archivo Markdown permite agregar registros, pero no implementa funciones para modificarlos o eliminarlos.
- El modo `--trace` puede mostrar información interna devuelta por las herramientas, incluida la respuesta de `make_quiz`.
- La prueba de quiz y guardado fue una integración manual entre varias ejecuciones, no una conversación persistente automatizada.

### Conclusión

En Lecture 03 pasé de utilizar un LLM que responde con el contexto disponible a construir un agente capaz de consultar herramientas y ejecutar acciones.

La comparación con Lecture 01 demostró el valor de recuperar información específica del curso. Además, la implementación de HITL permitió comprender cómo incorporar decisiones humanas antes de ejecutar operaciones que modifican archivos.

Las pruebas funcionales y automatizadas ayudaron a identificar y corregir un problema relacionado con los reintentos posteriores a un rechazo.

Esta práctica reforzó mis conocimientos sobre agentes de IA, herramientas, ciclos de ejecución, trazabilidad, aprobación humana y diseño de pruebas de calidad.

### Hallazgo adicional sobre las instrucciones del agente:

Durante las pruebas observé que el agente, aunque consultaba correctamente el glosario, en ocasiones limitaba demasiado sus explicaciones. Por ello, ajusté sus instrucciones para permitir complementar los conceptos técnicos con conocimiento general y ejemplos prácticos, manteniendo el glosario como referencia principal para la información oficial del curso. Intenté validar el cambio mediante una prueba de regresión, pero no fue posible completarla debido a la saturación del modelo. Por tanto, la mejora queda implementada, pero pendiente de verificación funcional.