# Lecture 02: resultados de referencia (obtenidos por el docente en una T4 con la versión original en japonés)

Si no se te asigna una GPU o el entrenamiento no termina a tiempo, sigue el apartado **4b** del cuaderno (`notebooks/lora_format_tuning.ipynb`) y continúa la comparación y el análisis con los resultados de esta carpeta.
Al entregar, establece `executed_training_myself` de la sección 7 en `False` e indica en `lectures/02/answer.md` hasta dónde pudiste ejecutar por tu cuenta.

| Archivo | Contenido |
|---|---|
| `result.json` | Configuración (`config`), versiones de bibliotecas, resúmenes antes y después del entrenamiento (`before` / `after`), preguntas con regresión y resultados de las preguntas de conocimiento |
| `eval_before.json` | Salidas originales y puntuación de las 21 preguntas antes del entrenamiento |
| `eval_after.json` | Salidas originales y puntuación de las 21 preguntas después del entrenamiento |

- Abre los archivos en GitHub o guárdalos con «Download raw file»
- Incluso con la misma semilla, el entrenamiento en GPU no se reproduce de forma exacta. Es normal que tus «preguntas con fallos restantes» difieran de las de referencia. Compara los tipos de fallos
