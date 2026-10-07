# Guía Senior de IA Generativa en Google Cloud

Guía de referencia para un **Senior AI Engineer** en Google Cloud: qué hay en la plataforma, qué conceptos debes poder explicar, cómo decidir entre alternativas, qué comandos usar y qué preguntas esperar en una entrevista. Cada tema apunta al micro lab o ejemplo donde se practica.

- Micro labs GenAI: `03` (chatbot), `04` (pipeline de documentos), `12` (RAG en BigQuery), `13` (Vertex AI Search), `14` (agente ADK), `15` (Model Armor), `16` (tuning, batch y evaluación)
- Ejemplos SDK: [../sdk-examples](../sdk-examples) (01-19)

---

## 1. Mapa de la plataforma

| Capa | Servicio | Para qué | Práctica |
|---|---|---|---|
| Modelos | **Gemini** en Vertex AI (Pro, Flash, Flash-Lite) | Texto, código, multimodal, razonamiento (*thinking*) | sdk 01-08, lab 03 |
| | **Model Garden** | Modelos de Google, open models (Gemma, Llama…) y de terceros; despliegue en endpoints | — |
| | **Imagen / Veo / Chirp** | Imagen, video y voz | sdk 15 |
| | **Embeddings** (`gemini-embedding-001`, `text-multilingual-embedding-002`) | Búsqueda semántica, clustering, clasificación | sdk 05, lab 12 |
| Conocimiento (RAG) | **Vertex AI Search** (AI Applications) | RAG administrado: parsing, chunking, ranking, citas | lab 13 |
| | **Vertex AI RAG Engine** | RAG administrado con control del corpus y del vector store | — |
| | **Vector Search** | Índice vectorial ANN a gran escala y baja latencia | — |
| | **BigQuery Vector Search** / **AlloyDB pgvector** | Vectores junto a tus datos (SQL) | lab 12 |
| Agentes | **ADK** (Agent Development Kit) | Framework open source de agentes (herramientas, sesiones, multi-agente) | lab 14 |
| | **Vertex AI Agent Engine** | Runtime administrado de agentes (sesiones, memoria, escalado, trazas) | lab 14 (README) |
| | **MCP / A2A** | Herramientas externas (MCP) y comunicación entre agentes (A2A) | — |
| Calidad | **Gen AI Evaluation Service** | Métricas automáticas y LLM-as-judge | lab 16, sdk 09/19 |
| | **Tuning** (SFT con LoRA, preference tuning) | Ajustar Gemini a una tarea o estilo | lab 16 |
| Seguridad | **Model Armor** | Prompt injection, jailbreak, contenido dañino, SDP, URLs | lab 15 |
| | **Safety settings** del modelo | Umbrales por categoría | sdk 18 |
| | **VPC-SC, CMEK, Private Service Connect, IAM** | Perímetro de datos, llaves propias, acceso privado | lab 11 |
| Operación | **Batch prediction**, **context caching**, **provisioned throughput** | Costo y capacidad | sdk 14, lab 16 |
| | Cloud Logging/Monitoring/Trace | Tokens, latencia, errores, SLOs | lab 07 |

## 2. Conceptos que debes poder explicar

### Modelo y generación

| Concepto | Explicación breve |
|---|---|
| Tokens | Unidad de cobro y de límite. Entrada + salida (+ *thinking*). `count_tokens` estima antes de llamar (sdk 08). |
| Ventana de contexto | Máximo de tokens por petición. Contexto largo ≠ gratis: más costo y latencia, y la atención se degrada con relleno irrelevante. |
| temperature / top_p / top_k | Aleatoriedad del muestreo. Bajo para extracción y clasificación, más alto para creatividad. |
| `max_output_tokens` | Tope de costo y de latencia por respuesta. |
| *Thinking* (razonamiento) | Los modelos 2.5 razonan antes de responder; `thinking_budget` controla tokens extra, calidad vs costo (sdk 08). |
| System instruction | Rol, reglas y formato persistentes; no es una frontera de seguridad. |
| Salida estructurada | `response_schema` (Pydantic/JSON Schema) en lugar de "responde en JSON" (sdk 04). |
| Function calling | El modelo propone llamadas; tu código ejecuta. Base de los agentes (sdk 03). |
| Grounding | Anclar respuestas a fuentes (Google Search o tus datos) con metadata de citas (sdk 13, lab 13). |
| Multimodalidad | Imágenes, PDF, audio y video como entrada (por URI de GCS o bytes) (sdk 07). |

### RAG

| Concepto | Explicación breve |
|---|---|
| Pipeline | Ingesta → parsing → chunking → embeddings → índice → recuperación → (re-ranking) → generación con citas. |
| Chunking | Por tamaño, por estructura (layout) o semántico; con overlap. El tamaño depende del tipo de pregunta. |
| Búsqueda híbrida | Vectorial (semántica) + palabras clave (BM25): mejor para nombres propios y códigos. |
| Re-ranking | Un segundo modelo reordena los top-k recuperados: más precisión con poco costo. |
| Umbral de relevancia | No pasar contexto irrelevante; si no hay contexto, el modelo dice "no sé" (lab 12). |
| Evaluación de RAG | Recuperación (recall@k, MRR) y generación (groundedness/faithfulness, relevancia). |
| Riesgos | Contexto desactualizado, permisos (no recuperar lo que el usuario no puede ver), prompt injection indirecta. |

### Agentes

| Concepto | Explicación breve |
|---|---|
| Bucle de agente | Razonar → elegir herramienta → observar resultado → repetir → responder (lab 14). |
| Herramientas | Docstrings claros, argumentos validados, errores explícitos, idempotencia en escrituras. |
| Memoria | De sesión (conversación) y de largo plazo (preferencias, hechos); con TTL y privacidad. |
| Patrones | Agente único con herramientas, *router*, secuencial, paralelo, *loop* (revisor), jerárquico (sub-agentes). |
| Guardrails de agentes | Confirmación humana para acciones irreversibles, límite de pasos, mínimo privilegio, auditoría de cada llamada. |
| MCP | Protocolo estándar para exponer herramientas y datos a modelos/agentes. |
| A2A | Protocolo para que agentes de distintos equipos o proveedores colaboren. |

### Calidad, seguridad y operación (LLMOps)

| Concepto | Explicación breve |
|---|---|
| Evaluación continua | Dataset dorado + métricas + quality gate en CI antes de cambiar prompt o modelo (sdk 09, 19). |
| LLM-as-judge | Rúbrica explícita, temperatura 0, salida estructurada; validar contra humanos. |
| Fine-tuning | Cuando el prompting no logra formato o estilo consistente o hay que bajar costo; SFT con LoRA (lab 16). |
| Alucinaciones | Grounding, umbrales de relevancia, "no sé" explícito, temperatura baja, validación de salida. |
| Prompt injection | Directa e indirecta; Model Armor + separación de instrucciones y datos + mínimo privilegio (lab 15). |
| Responsible AI | Safety settings, filtros, transparencia, revisión humana en decisiones de alto impacto. |
| Datos | Vertex AI no usa tus datos para entrenar modelos base; residencia por región, CMEK, VPC-SC. |
| Cuotas | RPM/TPM por modelo y región; backoff con jitter (sdk 16); *provisioned throughput* para capacidad garantizada. |
| Costo | Modelo más pequeño que cumpla, `max_output_tokens`, caching (sdk 14), batch (lab 16), historial truncado, routing por dificultad. |
| Latencia | Streaming (TTFT), modelos Flash, `thinking_budget` bajo, prompts cortos, ubicación cercana. |
| Observabilidad | Loguear tokens, latencia, modelo, `finish_reason`, bloqueos; trazas por paso del agente; SLOs (lab 07). |

## 3. Decisiones típicas

### Prompting vs RAG vs fine-tuning

| Necesidad | Solución |
|---|---|
| Mejorar instrucciones, formato o tono | Prompt engineering + salida estructurada |
| Conocimiento privado o que cambia seguido | **RAG** |
| Información pública reciente | Grounding con Google Search |
| Formato o estilo muy específico y consistente, o reducir costo/latencia con un modelo pequeño | **Fine-tuning** (SFT/LoRA) o destilación |
| Ejecutar acciones en sistemas | Function calling / agente |

### ¿Qué RAG uso en Google Cloud?

| Opción | Úsala cuando | Lab |
|---|---|---|
| BigQuery Vector Search | Tus datos ya viven en BigQuery; volumen moderado; equipo SQL | 12 |
| AlloyDB / Cloud SQL con pgvector | Aplicación transaccional que necesita vectores junto a sus tablas | — |
| Vertex AI Vector Search | Millones o miles de millones de vectores, latencia de milisegundos | — |
| Vertex AI RAG Engine | Quieres RAG administrado pero controlando el corpus y el vector store | — |
| Vertex AI Search | Búsqueda empresarial lista: conectores, layout parser, ranking, citas | 13 |

### ¿Dónde corre mi aplicación GenAI?

| Opción | Úsala cuando |
|---|---|
| Cloud Run / Cloud Run functions | APIs y agentes stateless, escala a cero (labs 03, 12-15) |
| Vertex AI Agent Engine | Agentes con sesiones/memoria administradas |
| GKE | Modelos open source propios con GPU, control total (lab 06 como base) |
| Batch prediction / Workflows | Procesamiento masivo o asíncrono (labs 04, 16) |

## 4. Arquitectura de referencia de una aplicación GenAI

```
Usuarios ─► Cloud Armor / API Gateway (cuotas, auth)
             ─► Cloud Run (orquestador / agente ADK)
                  ├─ Model Armor: revisa entrada y salida
                  ├─ Retrieval: Vertex AI Search | Vector Search | BigQuery (con filtros de permisos)
                  ├─ Gemini (Vertex AI) con grounding, salida estructurada y tools
                  ├─ Herramientas: APIs internas, BigQuery, Firestore (IAM mínimo)
                  └─ Memoria: Agent Engine sessions / Firestore (TTL)
             ─► Logging de tokens, latencia, bloqueos y trazas → Monitoring (SLOs) → BigQuery (análisis de costos)
Offline: datasets dorados → evaluación (CI) → tuning/batch → despliegue controlado (A/B, canary)
Seguridad: VPC-SC, CMEK, IAM por servicio, Secret Manager, auditoría (lab 11)
```

## 5. Comandos esenciales

```bash
# Proyecto y credenciales
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
gcloud services enable aiplatform.googleapis.com discoveryengine.googleapis.com modelarmor.googleapis.com

# Llamar a Gemini por REST (útil para depurar sin SDK)
curl -s -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  "https://aiplatform.googleapis.com/v1/projects/$PROJECT/locations/global/publishers/google/models/gemini-2.5-flash:generateContent" \
  -d '{"contents":[{"role":"user","parts":[{"text":"Hola"}]}]}'

# Vertex AI
gcloud ai models list --region=us-central1
gcloud ai endpoints list --region=us-central1
gcloud ai batch-prediction-jobs list --region=us-central1
gcloud ai tuning-jobs list --region=us-central1            # o client.tunings.list()

# BigQuery ML + vectores
bq query --use_legacy_sql=false 'SELECT * FROM ML.GENERATE_EMBEDDING(MODEL `ds.embedding_model`, (SELECT "hola" AS content))'
bq query --use_legacy_sql=false 'SELECT * FROM VECTOR_SEARCH(TABLE `ds.chunks`, "embedding", (SELECT ...), top_k => 5)'

# Agentes (ADK)
pip install google-adk
adk create mi_agente && adk web && adk run mi_agente
adk deploy agent_engine --project=$PROJECT --region=us-central1 mi_agente
adk deploy cloud_run --project=$PROJECT --region=us-central1 mi_agente

# Model Armor
gcloud model-armor templates list --location=us-central1

# Despliegue rápido de una app (sin Dockerfile)
gcloud run deploy mi-app --source . --region us-central1 --no-allow-unauthenticated

# Observabilidad
gcloud logging read 'resource.type="cloud_run_revision" AND jsonPayload.output_tokens>0' --limit 10
```

## 6. Preguntas de entrevista (con respuesta corta)

1. **¿Cómo reduces alucinaciones?** Grounding (RAG o Search), umbral de relevancia, instrucción de responder "no sé", temperatura baja, salida estructurada validada y evaluación de groundedness.
2. **Gemini API vs Vertex AI?** Vertex AI: IAM, VPC-SC, CMEK, residencia de datos, cuotas empresariales, SLA e integración con el resto de GCP. La Gemini API con API key sirve para prototipos.
3. **¿Cómo eliges el tamaño de chunk?** Según el tipo de pregunta y el documento; se evalúa con recall@k sobre un set de preguntas reales. Usa overlap y chunking por estructura cuando hay títulos y tablas.
4. **¿Cuándo fine-tuning en lugar de RAG?** Cuando el problema es de formato, estilo o tarea (no de conocimiento), o para bajar costo y latencia con un modelo más pequeño.
5. **¿Cómo evalúas un sistema GenAI?** Dataset dorado versionado, métricas por componente (recuperación y generación), LLM-as-judge con rúbrica, costo y latencia, quality gate en CI y monitoreo en producción.
6. **¿Cómo controlas el costo?** Modelo mínimo suficiente, `max_output_tokens`, context caching, batch, historial truncado, routing por dificultad, límites de instancias y alertas de tokens.
7. **¿Cómo proteges contra prompt injection?** Model Armor en entrada, salida y contexto recuperado; separar instrucciones de datos; herramientas con mínimo privilegio y confirmación humana; nunca confiar en la instrucción de sistema como control de seguridad.
8. **¿Cómo diseñas las herramientas de un agente?** Pocas y con un propósito claro, docstrings que digan cuándo usarlas y cuándo no, validación de argumentos, idempotencia, errores explícitos y auditoría.
9. **¿Cómo manejas las cuotas 429?** Backoff exponencial con jitter, límite de concurrencia, colas, distribución entre regiones o endpoint global, y *provisioned throughput* si la carga es predecible.
10. **¿Qué loguearías de cada llamada?** Modelo y versión, tokens de entrada/salida/razonamiento, latencia, `finish_reason`, bloqueos de seguridad, herramientas llamadas y un identificador de traza. No guardes PII ni prompts completos sin necesidad.
11. **¿Cómo despliegas un cambio de prompt de forma segura?** Versionar el prompt, evaluarlo contra el dataset dorado, desplegar por canary o A/B y monitorear métricas de calidad y costo.
12. **¿Qué es grounding con Google Search y qué riesgo tiene?** Gemini busca en la web y cita; el riesgo es depender de fuentes externas no controladas y de su calidad. Muestra las fuentes al usuario.
13. **¿Cómo implementas permisos en RAG?** Filtrar en la recuperación por metadatos de acceso del usuario (ACL), nunca después de generar.
14. **¿Qué es destilación?** Usar un modelo grande para generar respuestas de alta calidad y ajustar con ellas un modelo pequeño más barato.
15. **¿Batch u online?** Batch para grandes volúmenes sin requisito de tiempo real (~50 % más barato); online para interacción.

## 7. Plan de práctica sugerido (2 semanas)

| Día | Práctica |
|---|---|
| 1 | sdk 01, 02, 08, 12: tokens, streaming, thinking, chat |
| 2 | sdk 04, 03, 17: salida estructurada, function calling, code execution |
| 3 | sdk 05, 06 + lab 12: RAG desde cero en BigQuery |
| 4 | lab 13 + sdk 13: RAG administrado y grounding; compara con el lab 12 |
| 5 | lab 14: agente con ADK; agrega una herramienta propia |
| 6 | lab 15 + sdk 18: seguridad (Model Armor y safety settings) |
| 7 | sdk 09, 19 + lab 16 (evaluate): evaluación |
| 8 | lab 16: batch y (opcional) fine-tuning |
| 9 | sdk 14, 16: costo y producción (caching, cuotas) |
| 10 | lab 07: SLOs y alertas sobre una app GenAI |
| 11-12 | Proyecto integrador: agente ADK + RAG (lab 12/13) + Model Armor + evaluación en CI |
| 13-14 | Repaso de esta guía y de las preguntas de entrevista |
