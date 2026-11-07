# Lecture 01: ejercicios y tarea — preparar el entorno de desarrollo y hacer preguntas al LLM

## Objetivos de esta sesión

- Abrir tu fork en Codespaces y llamar a Gemini API
- Hacer pequeños cambios en el código con GitHub Copilot
- Entregar el trabajo mediante un PR desde tu rama de trabajo (seguiremos este procedimiento en las demás sesiones)

## Qué necesitas

- Una cuenta personal de GitHub (en las cuentas administradas por empresas, la configuración de la organización puede impedir el uso de Codespaces o Copilot)
- Una cuenta personal de Google (en las cuentas corporativas de Google Workspace, la configuración del administrador puede impedir el uso de AI Studio)

## Ejercicios (45 minutos)

### 1. Crear un fork del repositorio del curso

Usa **Fork**, en la esquina superior derecha del repositorio del curso, para crear un fork en tu cuenta. A partir de ahora, trabajarás siempre en tu propio fork.

### 2. Generar una clave de Gemini API

Crea una clave API en [Google AI Studio](https://aistudio.google.com/apikey) y cópiala.

> La clave API es información secreta. No la pegues en el código, en el chat ni en commits. Si se filtra, elimínala en AI Studio y crea otra.

### 3. Registrarla como secret de Codespaces

En **Settings → Codespaces → Secrets → New secret** de GitHub, introduce lo siguiente.

- Name: `GEMINI_API_KEY`
- Value: la clave del paso 2
- Repository access: selecciona **tu propio fork**

> Registra el secret antes de iniciar Codespaces. Si lo registras después, tendrás que reiniciar Codespaces.

### 4. Iniciar Codespaces

En tu fork, selecciona **Code → Codespaces → Create codespace on main**. La primera preparación del entorno tarda unos minutos. Ejecuta lo siguiente en el terminal y comprueba que las pruebas pasan.

```bash
uv run pytest -q
```

### 5. Hacer preguntas al LLM sin herramientas

```bash
uv run python -m app.ask "¿Qué es LoRA?"
uv run python -m app.ask "¿Qué son los «3 niveles» de las tareas del curso AIE2026?"
```

La primera pregunta trata sobre un término general, así que la respuesta debería ser bastante correcta. La segunda pregunta trata sobre los «3 niveles de las tareas», algo específico del curso. Como el LLM sin herramientas no conoce el curso, puede responder «No lo sé» o dar una explicación general que suene convincente. La información correcta está en `homework-levels`, dentro de `data/glossary.json`. Compárala con la respuesta del modelo.

Si tienes tiempo, prueba otras preguntas específicas del curso. Observa que la respuesta a una misma pregunta puede cambiar en cada ejecución y que el modelo puede responder con seguridad incluso cuando no sabe algo.

```bash
uv run python -m app.ask "¿Qué es la «etiqueta lecNN-start» que se usa en el curso AIE2026?"
uv run python -m app.ask "¿Qué se aprende en Lecture 02 del curso AIE2026?"
```

### 6. Mostrar el número de tokens con Copilot

Modifica `app/ask.py` en el lugar marcado como `TODO(Lecture 01: ejercicio)` para que muestre el número de tokens de entrada y de salida. Puedes usar las sugerencias o el chat de Copilot. Lee y comprende el código propuesto antes de incorporarlo.

### 7. Crear una rama y un PR

```bash
git switch -c lec01
# Completa lectures/01/answer.md
git add -A
git commit -m "Lecture 01 exercises"
git push -u origin lec01
```

En tu fork de GitHub, crea un PR de `lec01` hacia `main`. **Comprueba que base repository sea tu propio fork** (no envíes el PR al repositorio del curso).

### 8. Detener Codespaces

Selecciona «Codespaces» en la esquina inferior izquierda → **Stop Current Codespace**. Si lo dejas en ejecución, seguirá consumiendo tu cuota gratuita.

## Tarea (basta con completar un nivel)

| Nivel | Contenido |
|---|---|
| Básico | Ejecuta cada pregunta 3 veces, cambia de modelo (con la variable de entorno `AIE_MODEL`) o cambia temperature, y resume las diferencias entre las respuestas en answer.md |
| Implementación | Modifica `app/ask.py` para poder seguir haciendo preguntas conservando el historial de conversación |
| Avanzado | Mide el tiempo de respuesta y el número de tokens, y compara varios modelos o preguntas. Analiza también su relación con los límites de uso de la cuota gratuita |

Ejemplo de cambio de modelo:

```bash
AIE_MODEL=gemini-3.5-flash uv run python -m app.ask "¿Qué es LoRA?"
```

### Notas adicionales sobre el modelo que utilizas

Las especificaciones de los modelos pueden cambiar.
La documentación de la API de Gemini se ha actualizado: Gemini 3.5 Flash ha quedado obsoleto y redirige a Gemini 3.6 Flash.

- Referencia: documentación de Gemini 3.5 Flash
https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash?hl=es

Como muestra este ejemplo, las especificaciones de los LLM ofrecidos como servicios cambian con frecuencia. Acostúmbrate a consultar la documentación del servicio para poder adaptarte a estos cambios.

Para la tarea de Lecture 01, puedes utilizar el modelo que prefieras.

Para cambiar temperature, investiga el argumento `config` de `generate_content`.
