# Lecture 02: ejercicios y tarea — aprender un formato de respuesta con LoRA y comparar antes y después del entrenamiento

Esta sesión se realiza en Google Colab (GPU T4, cuota gratuita). No se usa Codespaces.

## Objetivos de esta sesión

- Entrenar brevemente un modelo pequeño con LoRA y comprobar, con cifras y salidas, **qué cambia y qué no cambia** antes y después del entrenamiento
- Explicar con tus propios resultados que «el formato se puede aprender, pero el entrenamiento no garantiza que el modelo sepa cuándo pedir confirmación y cuándo responder con certeza ante lo que desconoce»
- Explicar con tus propias palabras cuándo conviene usar el ajuste fino y cuándo no

## Cuaderno que usaremos

- [notebooks/lora_format_tuning.ipynb](../../notebooks/lora_format_tuning.ipynb)
- Abrir en Colab: https://colab.research.google.com/github/matsuolab/lecture-ai-engineering-2026-es/blob/main/notebooks/lora_format_tuning.ipynb

Usaremos una FAQ ficticia de un curso (5 entradas) para entrenar `Qwen/Qwen3.5-0.8B` con LoRA durante 20 épocas (20 pasadas por 14 ejemplos, 40 pasos; en el experimento original en japonés tardó 4–5 minutos en una T4).
Los tiempos, las pérdidas y los comportamientos de salida citados proceden del experimento original en japonés. Pueden variar con la FAQ y las preguntas traducidas; registra y analiza tus propios resultados.

La salida deseada es una sola línea de JSON, `{"answer": ..., "needs_review": ...}`. Para las preguntas que no se resuelven en la FAQ, la respuesta correcta es indicar que «se necesita confirmación» con `needs_review: true`.
La evaluación distingue entre la **tasa de cumplimiento del formato** (si se respeta el formato JSON) y la **tasa de acierto del contenido** (si `needs_review` y las expresiones de la respuesta coinciden con la solución).

## Preparación previa (opcional, 5 minutos)

Antes de la clase, ejecutar las secciones 0–3 del cuaderno para comprobar la asignación de la GPU, la instalación de las bibliotecas y la descarga del modelo ayudará a evitar problemas durante la sesión.
En Colab, las variables se pierden al desconectarse la sesión, así que el día de clase volveremos a ejecutar desde la sección 0.

## Ejercicios (30 minutos)

1. Abre el cuaderno en Colab y crea una copia propia con **File → Save a copy in Drive**
2. Selecciona **Runtime → Change runtime type → T4 GPU**
3. Ejecuta las secciones 0–3 de arriba abajo (unos 5 minutos). Lee la tabla anterior al entrenamiento: **qué claves faltan** y si el texto coincide con la FAQ
4. Entrena el modelo en la sección 4 (4–5 minutos en el experimento original en japonés). Mientras esperas, lee la explicación sobre «la diferencia entre LoRA y QLoRA». Observa `trainable%` y la evolución de `Training Loss`
5. Evalúa el modelo entrenado en las secciones 5–6 y compáralo con el modelo sin entrenar
   - Tabla comparativa: cómo han cambiado `format_rate` y `content_rate`
   - `Regresiones`: preguntas que se superaban antes del entrenamiento y fallan después (lo deseable es que la lista esté vacía; examina las regresiones de tu propio experimento)
   - Tipos de fallos restantes: si el modelo **afirma** una respuesta reutilizando otra entrada de la FAQ para una pregunta sin evidencia, o si **elude** una pregunta que sí tiene evidencia diciendo «No se indica»
   - Sección 6: si pide confirmación o afirma una respuesta para preguntas ausentes tanto de la FAQ como de los datos de entrenamiento
6. Crea `result.json` en la sección 7. Escribe los puntos principales en `lectures/02/answer.md` y crea un PR desde la rama `lec02` hacia `main` de tu propio fork (puedes editar answer.md en la interfaz de GitHub). También puedes guardar `result.json` en `lectures/02/` e incluirlo en el PR
7. **Runtime → Disconnect and delete runtime**

> El tiempo de GPU disponible en la cuota gratuita de Colab es limitado. Elimina siempre el entorno de ejecución al terminar.
> Si no se te asigna una GPU o el entrenamiento no termina a tiempo, sigue el apartado 4b del cuaderno y continúa la comparación y el análisis con los resultados que el docente obtuvo en una T4 con la versión original en japonés. Al entregar, establece `executed_training_myself` en `False` e indica en answer.md hasta dónde pudiste ejecutar por tu cuenta.

Aunque se fije la semilla, el entrenamiento en GPU no se reproduce de forma exacta. Es normal que tus «preguntas con fallos restantes» difieran de las de otra persona; compara los tipos de fallos.

## Tarea (basta con completar un nivel)

| Nivel | Contenido |
|---|---|
| Básico | Cambia uno de los valores `lora_r`, `lr` o `num_train_epochs` de `CONFIG` y vuelve a entrenar. Registra `format_rate`, `content_rate`, la pérdida final y el tiempo de entrenamiento junto a la configuración original. Tras cambiarlo, selecciona **Runtime → Restart session** y ejecuta desde el principio (el modelo entrenado sigue en memoria). Compara los dos archivos `result.json` |
| Implementación | Sustituye `FAQ`, `GROUNDED` y `UNGROUNDED` por un tema propio (unas 5 entradas), entrena y compara antes y después. Conserva el formato JSON y el diseño de `needs_review`. Explica también cómo preparaste las preguntas «sin evidencia» |
| Avanzado | Usa `scripts/make_sft_dataset.py` para crear pares de preguntas y respuestas del glosario del curso (JSONL en formato `messages`) y entrena con ellos en lugar de la FAQ. Prepara tus propias preguntas de evaluación (términos del glosario, preguntas reformuladas y términos ausentes del glosario) y sus respuestas correctas, y compara antes y después. Compara el entrenamiento del modelo con un mecanismo de búsqueda en el glosario y analiza las ventajas y desventajas de entrenarlo |

Crear los datos para el nivel avanzado (ejecuta en Codespaces y sube el archivo generado a Colab):

```bash
uv run python scripts/make_sft_dataset.py > glossary_sft.jsonl
```

En Colab, cada línea tiene el mismo formato `messages` que `to_chat` en el cuaderno. Puedes pasar las líneas leídas directamente a `Dataset.from_list` y entrenar con `SFTTrainer` de la sección 4. Debes adaptar la evaluación (`test` y `gold`) al glosario.

La sección 8 (cargar en 4 bits y comparar las salidas) es una observación sin entrenamiento, por lo que puedes adjuntar sus resultados en cualquier nivel. El entrenamiento en 4 bits (QLoRA) queda fuera de la tarea porque no se ha verificado en el entorno de este curso (T4).

## Precauciones

- Después del entrenamiento, la variable `model` también tiene insertado el adaptador. Si necesitas volver a obtener las salidas anteriores al entrenamiento, usa `tuned.disable_adapter()` (véase la sección 6) o reinicia la sesión
- Las bibliotecas del cuaderno están fijadas a versiones verificadas (`PINS` en la sección 0). Cambiarlas puede impedir que funcione
