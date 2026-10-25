# Lecture 01: respuestas

## Ejercicios

- **Respuesta del modelo a la pregunta específica del curso (los 3 niveles de las tareas; basta con un resumen):** El modelo no identificó correctamente los tres niveles de AIE2026. En las primeras ejecuciones reconoció que no tenía información específica del curso y propuso clasificaciones educativas generales. Al cambiar de modelo, generó explicaciones más extensas y aparentemente seguras, pero igualmente incorrectas.

- **Qué observaste al compararla con la definición correcta del glosario:** Al comparar las respuestas con el archivo `data/glossary.json`, observé que Gemini confundió los niveles reales del curso con clasificaciones generales de dificultad o aprendizaje. El glosario establece tres opciones de tarea: **Básico**, para repasar el contenido de la clase; **Implementación**, para escribir código propio; y **Avanzado**, para investigar y experimentar. Además, indica que es suficiente realizar uno de estos niveles para completar la tarea y que, en principio, no se califica. Gemini no explicó correctamente esta estructura y, en algunas respuestas, incluso sugirió que los niveles determinaban diferentes calificaciones, algo que no corresponde a las reglas del curso.

- **Número de tokens que lograste mostrar (entrada / salida):** Con el modelo original y temperatura predeterminada de 1.0, la pregunta sobre AIE2026 consumió **21 tokens de entrada** en cada ejecución y generó **840, 720 y 614 tokens de salida**. 

- Para LoRA fueron **6 tokens de entrada** y **568, 626 y 654 de salida**.


## Tarea

- Nivel elegido: Básico / Implementación 

### Nivel Básico

- **Qué hiciste:** Ejecuté tres veces las mismas dos preguntas sobre LoRA y AIE2026 con `gemini-3.5-flash-lite` y temperatura 1.0. Después repetí las pruebas con temperatura 0.2 y finalmente cambié al modelo `gemini-3.5-flash`, manteniendo la temperatura en 0.2. Registré los tokens de entrada y salida y comparé las respuestas con `data/glossary.json`.

- **Resultados:**

  | Modelo | Temperatura | LoRA (salida) | AIE2026 (salida) |
  |---|---|---|---|
  | gemini-3.5-flash-lite | 1.0 | 568, 626, 654 | 840, 720, 614 |
  | gemini-3.5-flash-lite | 0.2 | 590, 538, 649 | 673, 575, 715 |
  | gemini-3.5-flash | 0.2 | 870, 770, 690 | 778, 906, 856 |

  Los tokens de entrada fueron siempre 6 para LoRA y 21 para AIE2026. Al reducir la temperatura, cambiaron la extensión y redacción de las respuestas. El modelo Flash generó respuestas más largas que Flash Lite, sin mejorar la precisión sobre los niveles del curso.

- **Observaciones y dudas:** LoRA es un concepto técnico ampliamente documentado, mientras que los niveles de AIE2026 requieren información específica del curso. Como el script no consulta Internet ni el glosario, el modelo pudo explicar LoRA correctamente, pero no recuperar las reglas particulares de AIE2026. Cambiar la temperatura o el modelo no solucionó esa falta de contexto. Además, durante las pruebas con Flash se presentaron errores de saturación HTTP 503, por lo que fue necesario repetir algunas solicitudes. Concluyo que una respuesta extensa y convincente no necesariamente es correcta y que resulta fundamental verificarla con una fuente confiable.

### Nivel Implementación

**Objetivo:**

Modificar `app/ask.py` para permitir realizar preguntas consecutivas al modelo, conservando el historial de conversación durante una misma sesión.

**Qué hiciste:**

Amplié el programa original para incorporar un modo de conversación interactiva mediante el argumento `--chat`, utilizando el SDK de Google Gen AI.

Los cambios principales fueron:

- Implementé la función `chat_loop()` para gestionar las preguntas consecutivas.
- Utilicé `client.chats.create()` para iniciar una sesión y `chat.send_message()` para enviar mensajes conservando el historial.
- Mantuve el modo original de preguntas individuales.
- Permití iniciar una conversación con o sin una pregunta inicial desde la terminal.
- Incorporé los comandos `salir`, `exit` y `quit` para finalizar la conversación.
- Agregué el manejo de `KeyboardInterrupt` y `EOFError` para cerrar la sesión sin mostrar errores cuando se interrumpe la entrada.
- Configuré una temperatura de `0.2` mediante la constante `TEMPERATURE`.
- Centralicé la visualización de tokens de entrada y salida en la función `show_usage()`.

**Cómo ejecutar el programa:**

Pregunta individual:

```bash
uv run python -m app.ask "¿Qué es LoRA?"
```

Pregunta predeterminada:

```bash
uv run python -m app.ask
```

Conversación con historial:

```bash
uv run python -m app.ask --chat
```

Conversación con una pregunta inicial:

```bash
uv run python -m app.ask --chat "¿Qué es LoRA?"
```

**Resultados de las pruebas funcionales:**

| Caso | Escenario | Resultado |
|---|---|---|
| CP01 | Ejecutar una pregunta individual | Aprobado |
| CP02 | Iniciar el chat sin pregunta inicial | Aprobado |
| CP03 | Iniciar el chat con pregunta inicial | Aprobado |
| CP04 | Realizar preguntas relacionadas conservando el contexto | Aprobado |
| CP05 | Presionar Enter sin escribir una pregunta | Aprobado |
| CP06 | Finalizar mediante `salir`, `exit` o `quit` | Aprobado |
| CP07 | Interrumpir la entrada con `Ctrl+C` | Aprobado después de una corrección |
| CP08 | Interrumpir la entrada con `Ctrl+D` | Aprobado después de una corrección |
| CP09 | Finalizar una conversación después de varios turnos | Aprobado |
| CP10 | Recuperar información del inicio de la conversación | Aprobado |
| CP11 | Ejecutar sin argumentos y mostrar la pregunta predeterminada | Aprobado |

**Evidencia de conservación del historial:**

Durante una prueba proporcioné al modelo el identificador `HIST-2026-KATH`.

Después realicé varias preguntas sobre LoRA y sus ventajas frente al fine-tuning completo.

Finalmente, pregunté:

> ¿Cuál era el identificador que te indiqué al comienzo?

El modelo respondió correctamente:

> Tu identificador de prueba es HIST-2026-KATH.

Esto permitió comprobar que el modelo podía recuperar información proporcionada al comienzo de la sesión, incluso después de varias interacciones.

**Consumo de tokens durante la prueba:**

| Interacción | Tokens de entrada | Tokens de salida |
|---|---:|---:|
| Registro del identificador | 22 | 104 |
| Pregunta sobre LoRA | 137 | 799 |
| Ventajas frente al fine-tuning completo | 949 | 882 |
| Recuperación del identificador | 1845 | 32 |
| Pregunta sobre el pénsum del curso | 1887 | 329 |

Observé que los tokens de entrada aumentaron a medida que avanzaba la conversación. Esto es consistente con el procesamiento del historial acumulado, ya que cada solicitud incorpora el contexto anterior además de la pregunta actual.

**Defectos encontrados y correcciones:**

1. **Interrupción con `Ctrl+C`:** inicialmente, al presionar esta combinación mientras el programa esperaba una pregunta, aparecía un traceback con `KeyboardInterrupt`. Se corrigió mediante un bloque `try/except` y se verificó que tanto `Ctrl+C` como `Ctrl+D` permitían finalizar limpiamente.

2. **Visualización de la pregunta predeterminada:** se detectó que el programa podía mostrar `[Pregunta] None` cuando se ejecutaba sin argumentos. Se corrigió para imprimir la variable `question`, que contiene la pregunta que realmente se envía al modelo.

3. **Duplicación de código:** se centralizó la configuración de temperatura y la visualización del consumo de tokens para facilitar el mantenimiento.

**Pruebas automatizadas:**

Ejecuté:

```bash
uv run pytest -q
```

Las 11 pruebas existentes finalizaron correctamente:

```text
11 passed, 1 warning
```

La advertencia correspondía a una dependencia del SDK de Google Gen AI bajo Python 3.14 y no impidió la ejecución.

Las funcionalidades nuevas del chat se validaron principalmente mediante pruebas manuales.

**Observaciones y dudas:**

El historial permitió que Gemini interpretara preguntas relacionadas sin necesidad de repetir todo el contexto. También comprobé que podía recuperar un identificador proporcionado varios turnos antes.

Sin embargo, observé que conservar el historial incrementa los tokens de entrada y, por tanto, puede aumentar el consumo de recursos.

Además, cuando pregunté por el pénsum específico del curso, el modelo reconoció que no tenía acceso a esa información y ofreció una descripción general de contenidos de AI Engineering. Esto confirmó que conservar el historial no equivale a proporcionar acceso a documentos externos.

También identifiqué que una temperatura baja, como `0.2`, puede reducir la variabilidad de las respuestas, pero no garantiza exactitud ni elimina las posibles alucinaciones.

**Conclusión:**

Se cumplió el objetivo del nivel Implementación al modificar `app/ask.py` para mantener conversaciones con historial durante una misma sesión.

El programa conserva la funcionalidad original de preguntas individuales, permite iniciar un chat interactivo, muestra los tokens utilizados y maneja distintas formas de finalización.

El historial se conserva mientras el programa está en ejecución, pero no se almacena de forma permanente después de cerrar la sesión.

Este ejercicio me permitió comprender mejor el funcionamiento de las sesiones de chat con LLMs, el manejo de argumentos en Python, las excepciones, el consumo de tokens y la importancia de realizar pruebas funcionales y de regresión.