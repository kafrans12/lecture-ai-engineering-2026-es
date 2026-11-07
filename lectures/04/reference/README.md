# Lecture 04: material de referencia

- `labels_instructor.jsonl`: etiquetas del docente. `note` explica el veredicto y los fallos introducidos deliberadamente.
  Las etiquetas del docente no son necesariamente la respuesta correcta. Sirven para observar que también hay desacuerdos entre personas.

Para compararlas con tus etiquetas (`lectures/04/labels.jsonl`), usa la pantalla «Comparar» de `tools/annotate.py` o este comando:

```bash
uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl
```

## Observaciones de la evaluación real (gemini-3.5-flash-lite)

Estas observaciones proceden del experimento original en japonés; no representan una ejecución del LLM en español. Se obtuvieron ejecutando `app.judge` con las etiquetas del docente como «tus etiquetas» y sirvieron para corregir `rubric.md` y el conjunto de evaluación.

| Observación | Corrección |
|---|---|
| #02 Fundamento: asignó fail por «indicar Lecture 03 al final», incluido en el comportamiento esperado de referencia (la referencia a la sesión se comprueba por código) | Se eliminó «indicar Lecture NN al final» del comportamiento esperado y se añadió a rubric.md que no se incluye aquí la comprobación de Lecture NN |
| #06 y #08 Claridad: trasladó a este criterio los motivos de fail en Pistas o Ámbito | Se añadió a Claridad que solo evalúa la facilidad de lectura, mientras que otros criterios evalúan el contenido y la función; también se indicó que los criterios se evalúan de forma independiente |
| #04 Claridad: aprobó una respuesta redundante que repetía la misma explicación | Se concretó que repetir o reformular lo mismo, por ejemplo con «Es decir», merece fail |
| #05 Fundamento: devolvió pass en vez de unsure, decidiendo por su cuenta un asunto no resuelto por los criterios | Se añadió al final de rubric.md «Asuntos pendientes de decidir» y se indicó que los casos correspondientes reciben unsure. En el PASO 3 se decide una política y se añade a los criterios |

El modelo evaluador tiende a decidir pass o fail incluso en asuntos no resueltos por los criterios. Antes de la clase, vuelve a ejecutar con la rúbrica corregida y comprueba si #05 recibe unsure.
