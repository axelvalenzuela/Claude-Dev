# Rutas de aprendizaje

Recorridos sugeridos por objetivo. Cada paso apunta a un lab o micro lab concreto.

## Ruta 1: AI Engineer en Google Cloud

Objetivo: dominar el desarrollo con IA generativa en Google Cloud, desde el SDK hasta producción.

| Paso | Lab | Lo que logras |
|---|---|---|
| 1 | [lab09-gemini-sdk-basico](../04-ia-generativa/lab09-gemini-sdk-basico/) | Primeras llamadas, system instructions, tokens, *thinking* |
| 2 | [lab08-curso-ia · parte 1](../04-ia-generativa/lab08-curso-ia/parte1_fundamentos/) | Tokens, embeddings, generación y RAG explicados en Python puro |
| 3 | [sdk-examples GCP 01-11](../03-cloud-e-infraestructura/lab11-terraform-gcp/sdk-examples/) | Streaming, function calling, salida estructurada, embeddings, RAG, multimodal, evaluación |
| 4 | [lab08-curso-ia · parte 2](../04-ia-generativa/lab08-curso-ia/parte2_gcp/) | Vertex AI SDK, agentes, multi-agente con ADK, evaluación con quality gate |
| 5 | [lab07-rag-vertex-cloudrun](../04-ia-generativa/lab07-rag-vertex-cloudrun/) | Aplicación RAG completa desplegada en Cloud Run |
| 6 | [lab11 · 03 chatbot](../03-cloud-e-infraestructura/lab11-terraform-gcp/microlabs/03-genai-chatbot-vertex-gemini/) y [04 pipeline](../03-cloud-e-infraestructura/lab11-terraform-gcp/microlabs/04-genai-docs-workflows/) | Chatbot con memoria y guardrails; pipeline de documentos con Workflows |
| 7 | [lab11 · 12 RAG en BigQuery](../03-cloud-e-infraestructura/lab11-terraform-gcp/microlabs/12-genai-rag-bigquery-vector/) | RAG con vectores propios, umbral de relevancia y citas |
| 8 | [lab11 · 13 Vertex AI Search](../03-cloud-e-infraestructura/lab11-terraform-gcp/microlabs/13-genai-vertex-ai-search-grounding/) | RAG administrado y grounding; *build vs buy* |
| 9 | [lab11 · 14 agente ADK](../03-cloud-e-infraestructura/lab11-terraform-gcp/microlabs/14-genai-agent-adk/) | Agente con herramientas, memoria y Agent Engine |
| 10 | [lab11 · 15 Model Armor](../03-cloud-e-infraestructura/lab11-terraform-gcp/microlabs/15-genai-model-armor-safety/) | Seguridad de LLMs: injection, jailbreak, datos sensibles |
| 11 | [lab11 · 16 tuning, batch y evaluación](../03-cloud-e-infraestructura/lab11-terraform-gcp/microlabs/16-genai-tuning-batch-eval/) | Decidir con métricas entre prompting, RAG y fine-tuning |
| 12 | [sdk-examples GCP 12-19](../03-cloud-e-infraestructura/lab11-terraform-gcp/sdk-examples/) + [lab11 · 07 SLOs](../03-cloud-e-infraestructura/lab11-terraform-gcp/microlabs/07-sre-slo-monitoring/) | Producción: caching, cuotas, LLM-as-judge, observabilidad |

Repaso final: [Guía Senior GenAI en Google Cloud](../03-cloud-e-infraestructura/lab11-terraform-gcp/docs/SENIOR-GENAI-GCP.md) (conceptos, decisiones, comandos y preguntas de entrevista).

## Ruta 2: Cloud, DevOps y SRE

| Paso | Lab | Lo que logras |
|---|---|---|
| 1 | [lab05-kubernetes-local](../03-cloud-e-infraestructura/lab05-kubernetes-local/) | Objetos de Kubernetes y operación básica |
| 2 | [lab10 · 00 bootstrap](../03-cloud-e-infraestructura/lab10-terraform-aws/microlabs/00-platform-bootstrap-s3-oidc/) y [11 seguridad](../03-cloud-e-infraestructura/lab10-terraform-aws/microlabs/11-security-guardrails-rbac/) | Estado remoto, CI sin secretos, guardrails y RBAC |
| 3 | [lab10 · 01-05](../03-cloud-e-infraestructura/lab10-terraform-aws/microlabs/) | Serverless, eventos y GenAI en AWS |
| 4 | [lab10 · 06 tres niveles](../03-cloud-e-infraestructura/lab10-terraform-aws/microlabs/06-web3tier-alb-asg-rds/) y [07 SRE](../03-cloud-e-infraestructura/lab10-terraform-aws/microlabs/07-sre-slo-cloudwatch-fis/) | Arquitectura clásica, SLOs, burn rate y chaos engineering |
| 5 | [lab11 (GCP)](../03-cloud-e-infraestructura/lab11-terraform-gcp/) | Los mismos patrones en Google Cloud + GKE Autopilot |
| 6 | [lab10 · 09-10](../03-cloud-e-infraestructura/lab10-terraform-aws/microlabs/) y [lab11 · 09-10](../03-cloud-e-infraestructura/lab11-terraform-gcp/microlabs/) | Migración y gobernanza multi-cuenta/organización |
| 7 | [lab06-sap-s4hana-fiori](../03-cloud-e-infraestructura/lab06-sap-s4hana-fiori/) | Automatización de una plataforma empresarial |

Guía comparativa: [AWS ↔ GCP](../03-cloud-e-infraestructura/lab11-terraform-gcp/docs/GUIA-AWS-GCP.md).

## Ruta 3: Backend y aplicaciones web

| Paso | Lab | Lo que logras |
|---|---|---|
| 1 | [lab01-fastapi-todo](../01-desarrollo-web/lab01-fastapi-todo/) | API REST, validación y tests |
| 2 | [lab02-django-gastos-viaje](../01-desarrollo-web/lab02-django-gastos-viaje/) | Aplicación completa con roles, auditoría y despliegue |
| 3 | [lab10 · 01 API serverless](../03-cloud-e-infraestructura/lab10-terraform-aws/microlabs/01-serverless-apigw-lambda-dynamodb/) | El mismo tipo de API llevado a serverless con seguridad en capas |

## Ruta 4: MCP y automatización con Claude

| Paso | Lab | Lo que logras |
|---|---|---|
| 1 | [lab03-mcp-puppeteer](../02-mcp-y-agentes/lab03-mcp-puppeteer/) | Crear un servidor MCP propio |
| 2 | [lab04-kohi-multi-mcp](../02-mcp-y-agentes/lab04-kohi-multi-mcp/) | Combinar varios MCPs en un flujo real |
