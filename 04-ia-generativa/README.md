# 04 · IA generativa

Modelos de lenguaje con Gemini en Google Cloud: desde la primera llamada al SDK hasta RAG, agentes, evaluación y despliegue.

| Lab | Qué aprendes | Requiere |
|---|---|---|
| [lab09-gemini-sdk-basico](lab09-gemini-sdk-basico/) | Primeras llamadas con `google-genai`: generación, system instructions, conteo de tokens y *thinking* | API key de Gemini o Vertex AI |
| [lab08-curso-ia](lab08-curso-ia/) | 21 micro labs: fundamentos (tokens, embeddings, RAG) en Python puro y desarrollo en GCP (salida estructurada, agentes, multi-agente con ADK, evaluación, BigQuery, Cloud Run, Dataflow) | Python; GCP opcional (modo simulado gratis) |
| [lab07-rag-vertex-cloudrun](lab07-rag-vertex-cloudrun/) | Aplicación RAG completa: chunking, embeddings, búsqueda vectorial, API FastAPI con chat web y despliegue en Cloud Run con Terraform | Proyecto de GCP |

**Orden sugerido:** lab09 (SDK) → lab08 (conceptos y patrones) → lab07 (aplicación de punta a punta).

**Siguiente nivel (Senior AI Engineer):**

- Micro labs GenAI de [lab11-terraform-gcp](../03-cloud-e-infraestructura/lab11-terraform-gcp/): RAG con BigQuery Vector Search (12), Vertex AI Search y grounding (13), agente con ADK (14), Model Armor (15), fine-tuning + batch + evaluación (16).
- [19 ejemplos cortos del SDK](../03-cloud-e-infraestructura/lab11-terraform-gcp/sdk-examples/) (streaming, function calling, salida estructurada, context caching, grounding, LLM-as-judge…).
- [Guía Senior GenAI en Google Cloud](../03-cloud-e-infraestructura/lab11-terraform-gcp/docs/SENIOR-GENAI-GCP.md): conceptos, decisiones, comandos y preguntas de entrevista.
- Equivalentes en AWS: [ejemplos con Bedrock](../03-cloud-e-infraestructura/lab10-terraform-aws/sdk-examples/).
