# Lab 9 – Google Gen AI SDK: Gemini API y Vertex AI

Scripts cortos con el SDK `google-genai`. Cada uno enseña un concepto. El mismo código corre contra la **Gemini Developer API** (API key) o contra **Vertex AI** (proyecto de GCP); solo cambia el `.env`.

## Gemini Developer API vs Vertex AI

| | Gemini Developer API | Vertex AI |
|---|---|---|
| Autenticación | API key | IAM / ADC (`gcloud auth application-default login`) |
| Ideal para | Prototipos, aprendizaje | Empresa y producción |
| Región de datos | Global | Eliges región (`us-central1`, `europe-west4`…) |
| Safety `method` (SEVERITY/PROBABILITY) | No | Sí |
| Severidad en `safety_ratings` | No | Sí (`severity`, `severity_score`) |
| `labels` para costos | No | Sí |
| `compute_tokens` | No | Sí |
| Archivos | Bytes o Files API | URIs `gs://` de Cloud Storage |
| Extras empresariales | — | VPC-SC, CMEK, Model Armor, Provisioned Throughput, Batch, RAG Engine, Agent Engine |

## Configuración

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # y llena la opción A o la B
```

Para Vertex AI además:

```bash
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com --project TU_PROYECTO
```

> La API key **nunca** va en el código. `comun.py` la lee de `.env`, que está en `.gitignore`.

## Scripts (en orden sugerido)

| # | Script | Concepto |
|---|---|---|
| 1 | `gemini_call.py` | Primera llamada |
| 2 | `gemini_instruction.py` | System instruction (rol del modelo y primer guardrail) |
| 3 | `gemini_tokens.py` | `count_tokens`, `usage_metadata` y `compute_tokens` (Vertex) |
| 4 | `gemini_thinking.py` | `thinking_budget`, `include_thoughts` y su costo |
| 5 | `gemini_parametros.py` | `temperature`, `top_p`, `top_k`, `seed`, `stop_sequences`, `max_output_tokens` |
| 6 | **`gemini_safety.py`** | **Safety settings**: categorías, umbrales, método y cómo detectar bloqueos |
| 7 | `gemini_structured_output.py` | JSON con esquema Pydantic (`response.parsed`) |
| 8 | `gemini_function_calling.py` | Herramientas: modo automático y manual |
| 9 | `gemini_chat_streaming.py` | Chat multiturno con historial y streaming |
| 10 | `gemini_grounding.py` | Grounding con Google Search y fuentes |
| 11 | `gemini_embeddings.py` | Embeddings, `task_type` y búsqueda semántica (base de RAG) |
| 12 | `gemini_multimodal.py` | Imagen + texto (`gs://` en Vertex, bytes en Gemini API) |
| 13 | `vertex_produccion.py` | Reintentos con backoff, timeout, `labels` de costo y manejo de errores |

## Safety settings en resumen

| Categoría | Qué filtra |
|---|---|
| `HARM_CATEGORY_HARASSMENT` | Acoso, insultos dirigidos a una persona |
| `HARM_CATEGORY_HATE_SPEECH` | Odio contra grupos protegidos |
| `HARM_CATEGORY_SEXUALLY_EXPLICIT` | Contenido sexual explícito |
| `HARM_CATEGORY_DANGEROUS_CONTENT` | Instrucciones para causar daño (armas, drogas, etc.) |

| Umbral | Bloquea cuando el riesgo es… |
|---|---|
| `BLOCK_LOW_AND_ABOVE` | bajo, medio o alto (más estricto) |
| `BLOCK_MEDIUM_AND_ABOVE` | medio o alto |
| `BLOCK_ONLY_HIGH` | solo alto |
| `BLOCK_NONE` / `OFF` | nunca (`OFF` además no calcula el filtro) |

**Dónde se ve el bloqueo:**
- `response.prompt_feedback.block_reason`: se bloqueó el **prompt** y no hay `candidates`.
- `candidate.finish_reason == SAFETY`: se bloqueó la **respuesta**.
- `candidate.safety_ratings`: calificación por categoría.

**Buenas prácticas:**
- Define los umbrales de forma explícita; no dependas del default del modelo, que cambia entre versiones.
- Registra `finish_reason` y `safety_ratings` en tus logs.
- Muestra al usuario un mensaje amable cuando haya un bloqueo.
- Combina los filtros con una system instruction que acote el tema.
- En Vertex AI, agrega **Model Armor** contra prompt injection y fuga de datos.

## Siguiente paso

El proyecto `ai-engineer-gcp-aws/04-vertex-ai-projects` lleva estos conceptos a proyectos completos: RAG, agentes, evaluación, BigQuery, Cloud Run y gobernanza.
