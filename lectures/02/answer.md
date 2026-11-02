# Lecture 02: respuestas

> **Resumen del trabajo.** Se ejecutaron nueve experimentos de ajuste de hiperparámetros sobre la FAQ original (E0–E5, C1–C3), se seleccionó C2 para adaptar el modelo a una FAQ propia de aseguramiento de calidad (QA), y se evaluó por separado el modelo base con cuantización NF4 de 4 bits. Todas las cifras proceden de los archivos `result.json` y `eval_before_4bit.json` generados durante las ejecuciones.

## Ejercicios

### 1. Modelo y configuración utilizados (de `config` en `result.json`)

Se utilizó **`Qwen/Qwen3.5-0.8B`**, revisión `2fc06364715b967f1860aea9cf38778875588b17`, con **LoRA sin cuantización** para el entrenamiento principal. La revisión identifica la versión exacta del modelo y facilita reproducir el experimento.

| Parámetro | Valor seleccionado (C2 y QA) |
|---|---|
| Semilla (`seed`) | `42` |
| Épocas (`num_train_epochs`) | `10` |
| Pasos de calentamiento (`warmup_steps`) | `6` |
| Tasa de aprendizaje (`lr`) | `0.0002` |
| Rango LoRA (`lora_r`) | `4` |
| Escalado LoRA (`lora_alpha`) | `32` |
| Longitud máxima de secuencia (`max_seq_len`) | `512` |
| Máximo de tokens generados (`max_new_tokens`) | `96` |
| Generación (`do_sample`) | `false` (determinista) |

El entrenamiento de QA utilizó **1.597.440 parámetros entrenables (aprox. 0,212 % del total)**, con una ejecución de aproximadamente **130 segundos** en GPU T4. Estas cifras provienen del registro de entrenamiento de la práctica; no se incluyen en el resumen `result.json`.

### 2. ¿Ejecutaste el entrenamiento por tu cuenta? (`executed_training_myself`)

**Sí (`true`).** Ejecuté las nueve variantes originales, preparé el conjunto de datos propio de QA, entrené el adaptador LoRA, comparé las salidas antes y después, probé preguntas de control y ejecuté una prueba adicional de cuantización de 4 bits en Google Colab.

### 3. Antes y después del entrenamiento: `format_rate` y `content_rate`

**Evaluación principal de la implementación QA:** se probaron las mismas **21 preguntas** antes y después de entrenar. “Sin LoRA” corresponde al modelo base sin adaptador; “Con LoRA”, al modelo ajustado.

| Métrica | Sin LoRA | Con LoRA | Diferencia |
|---|---:|---:|---:|
| Formato JSON válido (`format_rate`) | 14/21 (66.67 %) | 21/21 (100.00 %) | +33.33 pp |
| Contenido aprobado (`content_rate`) | 10/21 (47.62 %) | 20/21 (95.24 %) | +47.62 pp |
| Formato y contenido (`both_rate`) | 10/21 (47.62 %) | 20/21 (95.24 %) | +47.62 pp |
| Tiempo de evaluación | 34.7 s | 49.1 s | — |

**Lectura del resultado.** Antes del entrenamiento, solo 14 respuestas cumplían el esquema JSON y 10 superaban ambas comprobaciones. Después, las 21 respuestas respetaron el esquema y 20 superaron ambas comprobaciones. El incremento de **47,62 puntos porcentuales** se refiere al conjunto concreto de preguntas de prueba, no a una garantía de desempeño general.

**Cómo se evaluó.** `format_rate` comprueba que la salida sea un objeto JSON con las claves `answer` (texto) y `needs_review` (booleano). `content_rate` contrasta las expresiones esperadas y el valor de `needs_review`; se normalizaron mayúsculas y tildes. `both_rate` exige pasar las dos comprobaciones. Este criterio automatizado no sustituye una revisión semántica humana y puede penalizar paráfrasis válidas o aprobar coincidencias superficiales.

### 4. Preguntas con regresión

En la implementación QA **no hubo regresiones registradas** (`regressed: []`): ninguna pregunta que antes aprobara ambas comprobaciones pasó a reprobarlas después. En la FAQ original sí se detectó una regresión en **E0, E4, E5 y C2**: «Explica cómo se tratan las entregas después de la fecha límite». El número de regresiones de cada experimento figura en la tabla de la Tarea.

### 5. Fallos restantes tras el entrenamiento y sus tipos

**Evaluación QA posterior a LoRA: 1 fallo de 21.**

| Pregunta | Comportamiento observado | Tipo de fallo |
|---|---|---|
| ¿Quién firma específicamente el acta de sign-off de UAT? | Repite los requisitos generales del sign-off y devuelve `needs_review: false`, aunque la FAQ no identifica al firmante. | **Afirmar sin evidencia suficiente** para el dato específico solicitado. |

No hubo errores de formato JSON en la evaluación posterior al entrenamiento. Tampoco se registraron en el conjunto principal preguntas con evidencia que fueran eludidas pidiendo confirmación. En controles adicionales apareció otro error de fundamentación, descrito a continuación.

### 6. Resultados de las preguntas de conocimiento (sección 6; antes → después)

| Pregunta de control | ¿Respuesta disponible en la FAQ? | Sin LoRA | Con LoRA | Interpretación |
|---|---|---|---|---|
| ¿Cuál es el tiempo máximo permitido para ejecutar UAT? | No | `format_error` | `needs_review` | **Correcto:** responde con información documentada. |
| ¿Qué herramienta específica se utiliza para registrar defectos? | No | `format_error` | `asserted` | **Correcto:** responde con información documentada. |
| ¿Quién es el responsable de aprobar el despliegue a producción? | No | `asserted` | `needs_review` | **Correcto:** responde con información documentada. |
| ¿Qué se necesita para iniciar UAT? | Sí | `asserted` | `asserted` | **Correcto:** responde con información documentada. |

**Resultado:** 3 de 4 controles quedaron correctamente clasificados tras LoRA. En particular, la FAQ dice que los defectos se registran en la herramienta definida por el proyecto, pero **no nombra una herramienta concreta**; responder esa frase con `needs_review: false` no satisface la pregunta «¿Qué herramienta específica...?».

### 7. Qué cambió y qué no cambió con el entrenamiento

**Cambió:** aumentó el cumplimiento del JSON (66,67 % → 100 %), mejoró la aprobación conjunta de formato y contenido (47,62 % → 95,24 %) y se corrigieron algunos comportamientos de abstención ante información no disponible.

**No cambió completamente:** el modelo aún confunde en ocasiones una respuesta general relacionada con el dato exacto solicitado. La coherencia del JSON no garantiza fundamentación; el ajuste tampoco aporta hechos que no estén presentes en la FAQ.

---

## Tarea

### 1. Nivel elegido: Básico / Implementación / Avanzado

**Nivel principal: Implementación**, con comparación de hiperparámetros del nivel básico. Además, realicé una **exploración opcional de cuantización NF4 de 4 bits**, sin entrenamiento QLoRA. No se presenta esta prueba como un ajuste fino cuantizado.

### 2. Configuración o datos que modificaste

**Actividad A — Experimentos sobre la FAQ original.** Se ejecutaron E0–E5 y C1–C3, variando las épocas (`5`, `10`, `20`), la tasa de aprendizaje (`0.0001`, `0.0002`, `0.001`) y el rango LoRA (`4`, `16`), manteniendo constantes el modelo base, la semilla, `lora_alpha=32` y la generación determinista.

**Actividad B — Selección de configuración.** C2 obtuvo 19/21 (90,48 %) al igual que C1, C3, E4 y E5. Se escogió como referencia por usar `r=4` (menos parámetros entrenables que `r=16`) con `lr=0.0002` y 10 épocas. **La elección no demuestra que C2 sea globalmente superior**: C2 tuvo una regresión en la FAQ original y C3 logró el mismo puntaje sin regresiones. La elección se evaluó de nuevo en QA.

**Actividad C — Adaptación a QA.** Se sustituyó la FAQ del curso por cinco temas: entrada a UAT, registro de defectos, severidad crítica, evidencia de fallos y sign-off. Se prepararon **14 ejemplos de entrenamiento**, **7 de validación** y **21 preguntas de prueba** (15 sobre información documentada y 6 fuera de la FAQ). La salida requerida fue un objeto JSON de una línea con `answer` y `needs_review`.

**Actividad D — Cuantización opcional.** Se cargó de nuevo el **modelo base sin adaptador** en NF4 de 4 bits con doble cuantización y cómputo `float16`; se ejecutó el mismo conjunto de 21 preguntas QA. Este ensayo evalúa inferencia cuantizada, no entrenamiento QLoRA.

### 3. Resultados (tabla comparativa o cifras)

#### 3.1. Los nueve experimentos originales: sin LoRA y con LoRA

Cada ejecución utilizó **21 preguntas** de la FAQ original. El modelo sin entrenar obtuvo **11/21 (52,38 %) de contenido y formato conjunto** en las nueve ejecuciones; el cumplimiento de formato fue **21/21 (100 %)** antes y después. La siguiente tabla muestra explícitamente la comparación del criterio conjunto (`both_rate`).

| Experimento | Épocas | `lr` | `r` | Sin LoRA (`both_rate`) | Con LoRA (`both_rate`) | Regresiones |
|---|---:|---:|---:|---:|---:|---:|
| E0 | 20 | 0.0002 | 16 | 11/21 (52.38 %) | 18/21 (85.71 %) | 1 |
| E1 | 5 | 0.0002 | 16 | 11/21 (52.38 %) | 18/21 (85.71 %) | 0 |
| E2 | 20 | 0.0010 | 16 | 11/21 (52.38 %) | 17/21 (80.95 %) | 0 |
| E3 | 20 | 0.0002 | 4 | 11/21 (52.38 %) | 18/21 (85.71 %) | 0 |
| E4 | 10 | 0.0002 | 16 | 11/21 (52.38 %) | 19/21 (90.48 %) | 1 |
| E5 | 20 | 0.0001 | 16 | 11/21 (52.38 %) | 19/21 (90.48 %) | 1 |
| C1 | 10 | 0.0001 | 16 | 11/21 (52.38 %) | 19/21 (90.48 %) | 0 |
| **C2** | 10 | 0.0002 | 4 | 11/21 (52.38 %) | 19/21 (90.48 %) | 1 |
| C3 | 10 | 0.0001 | 4 | 11/21 (52.38 %) | 19/21 (90.48 %) | 0 |

**Hallazgos.** Cinco configuraciones empataron con **19/21 (90,48 %)**. E2, con la tasa de aprendizaje más alta (`0.001`), obtuvo el menor resultado posterior (**17/21; 80,95 %**). Los resultados sugieren que aumentar épocas o rango LoRA no garantiza mejoras monotónicas en este conjunto pequeño. En todos los experimentos originales el formato ya era correcto antes del entrenamiento; la mejora observada se concentró en el contenido evaluado.

#### 3.2. Implementación QA: sin LoRA y con LoRA

| Métrica | Modelo base sin LoRA | Modelo entrenado con LoRA |
|---|---:|---:|
| Formato JSON | 14/21 (66.67 %) | 21/21 (100.00 %) |
| Contenido | 10/21 (47.62 %) | 20/21 (95.24 %) |
| Formato + contenido | 10/21 (47.62 %) | 20/21 (95.24 %) |

**Interpretación:** LoRA elevó el cumplimiento del contrato de salida y la puntuación de contenido para la FAQ de QA. Aun así, el error sobre el firmante del sign-off y el control sobre la herramienta específica muestran una limitación de fundamentación que debe abordarse antes de un uso operativo.

#### 3.3. Prueba opcional de 4 bits: modelo base sin LoRA

| Indicador | Modelo base sin cuantizar | Modelo base NF4 4 bits |
|---|---:|---:|
| Formato JSON | 14/21 (66.67 %) | 4/21 (19.05 %) |
| Contenido según evaluador | 10/21 (47.62 %) | 5/21 (23.81 %) |
| Formato + contenido | 10/21 (47.62 %) | 4/21 (19.05 %) |
| Tiempo de evaluación | 34.7 s | 36.3 s |
| Memoria reportada de pesos (`get_memory_footprint`) | 3,01 GB | 0,76 GB |

**Análisis de las 21 salidas NF4:** solo **4** cumplieron simultáneamente formato y contenido; **1** respuesta adicional fue aprobada en contenido, pero tenía una lista JSON como contenedor en lugar de un objeto. Se observaron respuestas en texto plano, arreglos JSON y valores booleanos aislados (`true`). Las **6 preguntas fuera de la FAQ** recibieron la frase apropiada de confirmación, pero en texto plano, por lo que incumplieron el contrato JSON y fueron rechazadas por el evaluador.

**Interpretación cautelosa:** el tamaño de memoria reportado bajó aproximadamente **74,8 %**, a costa de un fuerte deterioro del cumplimiento de formato en esta ejecución. `content_rate` penaliza respuestas que no se pueden interpretar con el esquema esperado, incluso cuando el texto es útil; por ello, **23,81 % no equivale a exactitud semántica humana**. Tampoco puede concluirse que QLoRA falle: **no se entrenó ni evaluó un adaptador sobre el modelo de 4 bits**.

### 4. Análisis de los casos en que conviene usar el ajuste fino y aquellos en que no

**Cuándo sí conviene.** LoRA resulta útil para reforzar un formato de salida repetible, adaptar el comportamiento a una tarea delimitada y aprovechar ejemplos de entrenamiento relativamente pequeños sin actualizar todos los parámetros del modelo. En esta práctica mejoró especialmente el seguimiento del esquema JSON y la respuesta a preguntas frecuentes de QA.

**Cuándo no es suficiente.** Si la información depende del proyecto o cambia con frecuencia —por ejemplo, nombres de herramientas, responsables de aprobación, SLA o criterios vigentes—, el ajuste fino no reemplaza la consulta de fuentes autorizadas. Para esos casos conviene combinar documentación recuperada y actualizada, reglas de validación, manejo explícito de incertidumbre y revisión humana cuando corresponda.

**Limitaciones y siguientes mejoras.** Los conjuntos son pequeños (21 preguntas de prueba por dominio); la evaluación de contenido se basa en frases clave y `needs_review`, no en un juicio semántico integral. Los experimentos originales y QA utilizaron datos distintos y algunas versiones de librerías diferentes, por lo que sus porcentajes no deben interpretarse como una comparación controlada entre dominios. Como siguiente iteración ampliaría las preguntas ambiguas y fuera de FAQ, validaría la fundamentación con personas expertas en QA y, si se busca evaluar QLoRA, entrenaría y probaría por separado un adaptador sobre el modelo cuantizado.

**Conclusión.** La práctica muestra una mejora clara de LoRA en el cumplimiento de formato y contenido de la FAQ QA (**10/21 → 20/21**), sin eliminar por completo los errores de fundamentación. La exploración de 4 bits demuestra una reducción de memoria reportada, pero no sustituye una comparación de modelos entrenados equivalentes.

### Hallazgo: limitaciones y mejoras del evaluador

Durante los experimentos identificamos algunas limitaciones en la evaluación automática:

- **Coincidencias textuales:** inicialmente, diferencias en mayúsculas y tildes generaban falsos negativos. Lo corregimos mediante normalización del texto.
- **Evaluación semántica:** el evaluador sigue utilizando palabras clave (`must_include`), por lo que puede rechazar respuestas correctas expresadas con otras palabras o aceptar respuestas incompletas.
- **Formato vs. contenido:** en la prueba de cuantización, algunas respuestas contenían información correcta, pero incumplían la estructura JSON requerida.
- **Fundamentación:** el evaluador no comprueba completamente si cada afirmación está respaldada por la FAQ.

**Conclusión:** aunque mejoramos la evaluación, las métricas automáticas no garantizan por sí solas la calidad de las respuestas. Como mejora futura, proponemos incorporar validación semántica, verificación de evidencia y revisión manual de casos ambiguos.
