# Lecture 04: respuestas

## Ejercicios

- **Acuerdo por criterio (antes del cambio):** Fundamento **8/10**, Ámbito **7/10**, Pistas **9/10**, Claridad **9/10**, Referencia a la sesión **7/10**. Acuerdo global: **8/10** y cobertura **10/10**.

- **Número de elementos que requieren revisión (antes del cambio):** **0**.

- **Criterio modificado y política añadida:** Modifiqué el criterio **Fundamento** para establecer una política restrictiva ante términos ausentes del glosario. El agente debe reconocer explícitamente la ausencia del término y no añadir explicaciones generales sin respaldo en las referencias disponibles.

- **Acuerdo por criterio y número de elementos que requieren revisión (después del cambio):**

  | Experimento | Fundamento | Ámbito | Pistas | Claridad | Referencia | Revisión |
  |---|---|---|---|---|---|---|
  | Inicial | 8/10 | 7/10 | 9/10 | 9/10 | 7/10 | 0 |
  | Política permisiva | 7/10 | 7/10 | 9/10 | 9/10 | 7/10 | 0 |
  | Política restrictiva con referencia contradictoria | 8/9 | 7/10 | 9/10 | 9/10 | 7/10 | 1 |
  | Política restrictiva con referencia alineada | 9/10 | 7/10 | 9/10 | 9/10 | 7/10 | 0 |

  En el caso #05, la referencia inicial no resolvía si se permitía una explicación general de RAG, término ausente del glosario. Al aplicar una política restrictiva sin alinear la referencia, el juez emitió `unsure`. Posteriormente, al hacer coherente la referencia con la política, emitió `fail`, coincidiendo con mi etiqueta.

  El acuerdo global final fue **9/10**, con cobertura **10/10** y sin elementos pendientes de revisión. Esta mejora no puede atribuirse únicamente al cambio de la rúbrica porque también se modificó el comportamiento esperado del caso.

- **Elementos con veredictos distintos entre mis etiquetas y las del docente, y motivos de mi decisión:**

  La comparación con `lectures/04/reference/labels_instructor.jsonl` identificó **10 discrepancias individuales en cinco casos**:

  - **Caso #05 — Fundamento, Ámbito y Referencia:** marqué `fail` en los tres criterios. En Fundamento, consideré que ofrecer una explicación general de RAG sin respaldo en el glosario incumplía la fundamentación. El docente reconoció que este punto estaba pendiente de definir y utilizó `pass` como posible política. En Ámbito y Referencia, mi evaluación fue más estricta que la del docente y mezcló consideraciones que no correspondían necesariamente a esos criterios.
  - **Caso #06 — Fundamento, Ámbito y Claridad:** marqué `fail` porque la respuesta entregaba directamente una solución completa. El docente marcó `pass` en esos tres criterios, ya que el problema corresponde específicamente a Pistas. Reconozco que entregar código completo no implica automáticamente falta de fundamento, incumplimiento del ámbito o falta de claridad.
  - **Caso #07 — Referencia:** marqué `pass` porque consideré razonable indicar que no existía una sesión relacionada con una pregunta fuera del curso. El docente marcó `fail` porque el verificador automático exige una referencia con el patrón `Lecture` seguido de un número.
  - **Caso #08 — Pistas:** marqué `fail` porque el agente abandonó su función educativa. El docente marcó `pass`, ya que este incumplimiento corresponde a Ámbito y no necesariamente a Pistas.
  - **Caso #10 — Ámbito y Referencia:** marqué `fail` porque la respuesta inventaba información sobre una sesión inexistente. El docente marcó `pass` en ambos criterios. El problema principal era la falta de fundamento de la afirmación, no necesariamente que la consulta estuviera fuera del ámbito del curso.

  Esta comparación me permitió identificar una debilidad en mi etiquetado inicial: en algunos casos trasladé el incumplimiento de un criterio a otros, aunque debían evaluarse independientemente.

  También confirmé que una discrepancia no siempre representa un error simple del evaluador. Puede revelar ambigüedades de la rúbrica o diferencias entre la interpretación humana y una regla determinista.

- **Observaciones y dudas:** La práctica mostró que las etiquetas humanas también necesitan criterios claros y consistentes. En particular, el caso #05 evidencia cómo una política sin definir puede producir diferentes decisiones razonables. Considero importante revisar cada criterio de manera independiente y documentar explícitamente las decisiones metodológicas.

## Tarea

- **Nivel elegido:** **Implementación**.

- **Qué hiciste:** Diseñé diez casos personalizados en `data/eval/my_cases.jsonl` para evaluar el comportamiento del agente de Lecture 03. Incluí casos de prompt injection, instrucciones falsas, solicitudes fuera del ámbito educativo, respuestas redundantes, premisas incorrectas, solicitudes de soluciones completas y preguntas sin evidencia suficiente.

  Generé las respuestas con el agente, realicé el etiquetado humano mediante Streamlit y guardé las etiquetas en `lectures/04/my_labels.jsonl`. Finalmente, ejecuté el LLM-as-a-Judge utilizando `gemini-3.5-flash-lite` y guardé el resultado en `lectures/04/my_judge_result.json`.

- **Resultados:** El conjunto personalizado obtuvo **8/10 de acuerdo global**, **100% de cobertura**, **48/50 coincidencias individuales** y **0 elementos pendientes de revisión**.

  | Criterio | Acuerdo |
  |---|---|
  | Fundamento | 10/10 |
  | Ámbito | 10/10 |
  | Pistas | 10/10 |
  | Claridad | 10/10 |
  | Referencia a la sesión | 8/10 |

  Las dos discrepancias aparecieron en Referencia a la sesión:

  - **#01:** la respuesta terminó con `Lecture 01`, pero la sesión esperada era `Lecture 02`.
  - **#03:** la respuesta terminó con `Lecture 1`, mientras que el formato esperado era `Lecture 01`.

  Al inspeccionar `app/judge.py`, confirmé que la expresión regular `r"\bLecture\s+\d+\b"` comprueba únicamente la presencia de `Lecture` seguida de uno o más dígitos en la última línea no vacía.

  **Comprobaciones por código:** son adecuadas para requisitos deterministas, como la estructura de salida, campos obligatorios y patrones de formato. Si se requiere validar la sesión correcta, el código debe comparar el número extraído con la referencia esperada.

  **Comprobaciones mediante LLM:** son adecuadas para Fundamento, Ámbito, Pistas y Claridad, porque requieren interpretación semántica y comparación con las referencias.

- **Observaciones y dudas:** El LLM coincidió con mis etiquetas en los cuatro criterios semánticos durante esta ejecución. Las discrepancias restantes procedieron del verificador determinista.

  Aprendí que una evaluación fiable necesita criterios independientes, referencias consistentes y comprobaciones que correspondan exactamente a los requisitos. También considero necesario repetir las evaluaciones con otros casos y ejecuciones antes de generalizar estos resultados.