# Ejemplos SDK para IA Engineer: Google Cloud (google-genai + Vertex AI)

Diecinueve scripts cortos (20-45 líneas), uno por concepto, con el SDK **`google-genai`** (el mismo que se usa con la Gemini API) sobre **Vertex AI**, más Pub/Sub y BigQuery. Cada archivo empieza con un docstring que explica el concepto, cómo correrlo y qué observar.

Los ejemplos 01-09 y 12-19 solo necesitan Vertex AI habilitado. Los 10-11 se conectan con los micro labs desplegados.

## Preparación (5 minutos)

```bash
cd 03-gemini-sdk/02-vertex-ai-examples
python -m venv .venv && source .venv/bin/activate      # Windows (Git Bash): source .venv/Scripts/activate
pip install -r requirements.txt
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com
export GOOGLE_CLOUD_PROJECT=<tu-proyecto>
python 01_gemini_generate.py
```

Variables opcionales: `GOOGLE_CLOUD_LOCATION` (default `global`), `GEMINI_MODEL` (default `gemini-2.5-flash`), `GEMINI_EMBED_MODEL` (default `gemini-embedding-001`).

## Índice

| # | Archivo | Concepto | Qué observar | Pregunta típica de entrevista |
|---|---|---|---|---|
| 01 | `01_gemini_generate.py` | Llamada básica en Vertex AI | `finish_reason`, tokens de entrada/salida | ¿Gemini API o Vertex AI en una empresa? ¿Por qué? |
| 02 | `02_gemini_streaming.py` | Streaming | Time to first token | ¿Cómo mejorarías la latencia percibida? |
| 03 | `03_gemini_function_calling.py` | Function calling automático con funciones de Python | El modelo encadena 2 funciones | ¿Qué riesgos tiene dejar que un agente ejecute código? |
| 04 | `04_gemini_structured_output.py` | Salida estructurada con Pydantic | `response.parsed` ya validado | ¿Cómo integras un LLM con un sistema que espera JSON? |
| 05 | `05_gemini_embeddings_search.py` | Embeddings con `task_type` | Documento correcto sin palabras en común | ¿Para qué sirve RETRIEVAL_QUERY vs RETRIEVAL_DOCUMENT? |
| 06 | `06_rag_minimo.py` | RAG con citas | Responde solo con el contexto | ¿Cómo evalúas un sistema RAG? |
| 07 | `07_gemini_multimodal.py` | Imagen + texto (URI de GCS) | La imagen también consume tokens | ¿Qué casos de uso resuelve la multimodalidad? |
| 08 | `08_gemini_tokens_thinking.py` | `count_tokens` + thinking budget | Tokens de razonamiento y su efecto en la respuesta | ¿Cómo controlas el costo de modelos que razonan? |
| 09 | `09_llm_evaluacion.py` | Evaluación con casos de prueba | Precisión y exit code para CI | ¿Qué es un quality gate para prompts? |
| 10 | `10_pubsub_publicar.py` | Eventos con schema (micro lab GCP 02) | Un mensaje inválido es rechazado | ¿Por qué validar el contrato del evento al publicar? |
| 11 | `11_bigquery_consulta.py` | Dry run de costo + consulta (micro lab GCP 08) | MB escaneados con partición y clustering | ¿Cómo controlas el costo en BigQuery? |
| 12 | `12_chat_multiturno.py` | Chat con historial (`client.chats`) | Los tokens de entrada crecen por turno | ¿Por qué una conversación larga cuesta más y cómo lo mitigas? |
| 13 | `13_grounding_google_search.py` | Grounding con Google Search | Fuentes web y búsquedas en `grounding_metadata` | ¿Cuándo grounding con Search y cuándo con tus datos? |
| 14 | `14_context_caching.py` | Context caching | `cached_content_token_count` y el TTL | ¿Cuándo conviene cachear contexto y cuándo no? |
| 15 | `15_imagen_generacion.py` | Generación de imágenes (Imagen) | Archivo PNG con marca SynthID | ¿Qué controles de seguridad tiene la generación de imágenes? |
| 16 | `16_async_concurrencia_reintentos.py` | Concurrencia + backoff con jitter | Reintentos ante 429/503 | ¿Cómo manejas las cuotas (RPM/TPM) en producción? |
| 17 | `17_code_execution.py` | Code execution (sandbox) | Código generado + resultado exacto | ¿Cómo evitas errores aritméticos de un LLM? |
| 18 | `18_safety_settings.py` | Safety settings y `finish_reason` | Categorías con riesgo y bloqueo | ¿Safety settings o Model Armor? ¿Por qué ambos? |
| 19 | `19_llm_as_judge.py` | LLM-as-judge con rúbrica | Calificación JSON por criterio | ¿Cómo evalúas respuestas abiertas a escala? |

## Ruta sugerida

1. **Fundamentos del modelo:** 01 → 02 → 08 → 09.
2. **Integración con sistemas:** 04 → 03.
3. **Conocimiento propio:** 05 → 06 → 07.
4. **Datos y eventos:** 10 → 11 con los micro labs 02 y 08.
5. **Nivel senior (producción):** 12 → 14 → 16 → 18 → 13 → 17 → 19 → 15, y después los micro labs GenAI 12-16.

## Retos para practicar

- 03: agrega una función que consulte BigQuery (ejemplo 11) y deja que el modelo responda preguntas de negocio.
- 06: usa los README de los micro labs como base de conocimiento.
- 08: mide la precisión del ejemplo 09 con `thinking_budget` 0 y 1024: ¿vale la pena el costo extra?
- Compara cada ejemplo con su equivalente en AWS: [07-bedrock-sdk](../../07-bedrock-sdk).
