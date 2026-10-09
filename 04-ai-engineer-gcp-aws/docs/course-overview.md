# Curso de IA: de cero a agentes en Google Cloud

[05-rag-app-cloud-run](../05-rag-app-cloud-run/) junta muchas piezas a la vez. Este lab las separa en **21 micro labs**, cada uno
con una sola idea, un archivo de instrucciones guiado y una sección de "qué hacer si algo falla".

- **Parte 1 — Fundamentos** (01–09): qué es aprender, redes neuronales, tokens, embeddings,
  cómo genera texto un LLM, RAG. Solo Python, sin instalar nada.
- **Parte 2 — Desarrollo de IA en GCP** (10–21): Vertex AI SDK, salida estructurada, RAG con
  embeddings, agentes, **multi-agente para migrar SAS → Python**, evaluación, BigQuery, Cloud
  Functions, Cloud Run, Dataflow, Composer, monitoreo. Corre **gratis en modo simulado** y se
  conecta a GCP cambiando una variable.

Está orientado a la vacante de *Senior AI Engineer — modernización SAS → Python/GCP*:
ver [docs/interview-guide.md](interview-guide.md).

## Empieza aquí

| Si quieres... | Lee |
|---|---|
| Aprender desde cero | [02-ai-fundamentals/](#parte-1--fundamentos) en orden |
| Construir con Vertex AI | [04-vertex-ai-projects/README.md](../04-vertex-ai-projects/README.md) |
| Saber cuánto cuesta y qué te falta para conectarte | [docs/gcp-costs.pdf](gcp-costs.pdf) · [docs/gcp-connect.md](gcp-connect.md) |
| Probar todo, paso a paso | [docs/testing-on-gcp.md](testing-on-gcp.md) |
| Preparar la entrevista | [docs/interview-guide.md](interview-guide.md) |
| Crear la infraestructura (Terraform) | [infra/README.md](../04-vertex-ai-projects/infra/README.md) |

Cada micro lab tiene **`README.md`** (la idea, qué observar, preguntas de entrevista) e
**`INSTRUCCIONES.md`** (paso a paso guiado, recorrido del código, tabla de errores, retos).

## Parte 1 — Fundamentos

Sin nube, sin API keys, sin `pip install`: solo Python 3.10+.

```bash
cd Claude-Dev/04-ai-engineer-gcp-aws
python 02-ai-fundamentals/01_reglas_vs_aprendizaje/spam.py
# ¿Sin Python? uv run --no-project --python 3.12 python 02-ai-fundamentals/01_reglas_vs_aprendizaje/spam.py
```

| # | Micro lab | La idea en una frase | Tiempo |
|---|---|---|---|
| 01 | [Reglas vs. aprendizaje](../02-ai-fundamentals/01_reglas_vs_aprendizaje/) | En vez de escribir la regla, el programa la saca de ejemplos. | 10 min |
| 02 | [Aprender = ajustar números](../02-ai-fundamentals/02_aprender_es_ajustar_numeros/) | Entrenar es mover parámetros poco a poco para bajar el error. | 15 min |
| 03 | [Una neurona](../02-ai-fundamentals/03_una_neurona/) | Una neurona suma entradas × pesos y decide sí/no. Tiene límites. | 10 min |
| 04 | [Red neuronal](../02-ai-fundamentals/04_red_neuronal/) | Varias neuronas en capas resuelven lo que una sola no puede. | 20 min |
| 05 | [Tokens](../02-ai-fundamentals/05_tokens/) | Los modelos leen pedazos de texto convertidos en números. | 15 min |
| 06 | [Embeddings](../02-ai-fundamentals/06_embeddings/) | El significado se representa como vector y se compara con coseno. | 15 min |
| 07 | [Siguiente palabra](../02-ai-fundamentals/07_siguiente_palabra/) | Un LLM solo predice el siguiente token, una y otra vez. | 15 min |
| 08 | [Temperatura](../02-ai-fundamentals/08_temperatura/) | Cómo se escoge el token: predecible vs. creativo. | 10 min |
| 09 | [Mini RAG](../02-ai-fundamentals/09_mini_rag/) | Buscar fragmentos relevantes y pegarlos al prompt. **05-rag-app-cloud-run en miniatura.** | 25 min |

## Parte 2 — Desarrollo de IA en Google Cloud

| # | Micro lab | Servicio | Concepto de la vacante |
|---|---|---|---|
| 10 | [setup_gcp](../04-vertex-ai-projects/10_setup_gcp/) | Proyecto, IAM, ADC | Entorno y diagnóstico |
| 11 | [gemini_sdk](../04-vertex-ai-projects/11_gemini_sdk/) | Vertex AI | LLMs, costo por token |
| 12 | [salida_estructurada](../04-vertex-ai-projects/12_salida_estructurada/) | Vertex AI | Business rule extraction |
| 13 | [embeddings_rag](../04-vertex-ai-projects/13_embeddings_rag/) | Vertex AI | RAG, contextual retrieval |
| 14 | [agente_herramientas](../04-vertex-ai-projects/14_agente_herramientas/) | Vertex AI | AI Agents |
| 15 | [multi_agente](../04-vertex-ai-projects/15_multi_agente/) | Vertex AI + ADK | Multi-agent orchestration, code conversion, validation, documentation |
| 16 | [evaluacion](../04-vertex-ai-projects/16_evaluacion/) | CI | Testing & QA of AI outputs |
| 17 | [bigquery](../04-vertex-ai-projects/17_bigquery/) | BigQuery + Terraform | SAS → BigQuery SQL, vector database |
| 18 | [cloud_functions_storage](../04-vertex-ai-projects/18_cloud_functions_storage/) | Storage, Functions | Event-driven automation |
| 19 | [cloud_run_api](../04-vertex-ai-projects/19_cloud_run_api/) | Cloud Run | REST APIs, production deployment |
| 20 | [composer_dataflow](../04-vertex-ai-projects/20_composer_dataflow/) | Dataflow, Composer | Pipelines y workflows |
| 21 | [monitoreo_gobernanza](../04-vertex-ai-projects/21_monitoreo_gobernanza/) | Logging, BigQuery | Monitoring, governance |

## Estructura

```
ai-engineer-gcp-aws/
├── 02-ai-fundamentals/   01–09 (solo biblioteca estándar)
├── 04-vertex-ai-projects/           10–21 + comun/ (código compartido) + tests/
├── infra/                Terraform: APIs, bucket, BigQuery, cuenta de servicio, presupuesto
├── docs/                 costos (PDF), conectar a GCP, cómo probar todo, guía de entrevista
├── scripts/              generar_costos.py (fuente única del PDF y del .md de costos)
└── ruff.toml             reglas del linter
```

## Mapa: de los micro labs a 05-rag-app-cloud-run

| Concepto | Micro lab | En 05-rag-app-cloud-run |
|---|---|---|
| Tokens y su costo | 05, 11 | [src/count_tokens.py](../05-rag-app-cloud-run/src/count_tokens.py) |
| Chunking | 09, 13 | [src/chunking.py](../05-rag-app-cloud-run/src/chunking.py) |
| Embeddings | 06, 13 | [src/gemini_client.py](../05-rag-app-cloud-run/src/gemini_client.py) |
| Similitud de coseno, top-k | 06, 09, 13 | [src/vector_store.py](../05-rag-app-cloud-run/src/vector_store.py) |
| Prompt con CONTEXTO | 09, 13 | [src/rag_engine.py](../05-rag-app-cloud-run/src/rag_engine.py) |
| Generación | 07, 08, 11 | [src/gemini_client.py](../05-rag-app-cloud-run/src/gemini_client.py) |
| Cloud Run, Terraform | 19, infra/ | `Dockerfile`, `infra/` |

> Nota: 05-rag-app-cloud-run usa `gemini-2.5-flash`, que Google retira alrededor del 16–20 de octubre de 2026.
> Estos labs usan `gemini-3.1-flash-lite` por defecto (configurable en `.env`).

## Glosario mínimo

| Término | Qué significa |
|---|---|
| **Modelo / parámetros** | Función con números ajustables; entrenar = ajustarlos con ejemplos |
| **Inferencia** | Usar un modelo ya entrenado (llamar a Gemini) |
| **Token** | Pedazo de texto que el modelo procesa como número; se cobra por token |
| **Embedding** | Vector que representa el significado de un texto |
| **LLM** | Red neuronal enorme entrenada para predecir el siguiente token |
| **Prompt / instrucción de sistema** | Lo que le mandas al modelo / sus reglas fijas |
| **Salida estructurada** | Respuesta JSON con un esquema fijo y validable |
| **RAG** | Buscar información relevante y dársela al modelo antes de que responda |
| **Agente** | LLM en un ciclo que decide y usa herramientas |
| **Multi-agente** | Varios agentes especializados coordinados por un orquestador |
| **Golden set** | Casos con respuesta conocida para medir calidad |
| **Reconciliación** | Comparar la salida migrada contra la salida original de SAS |
| **Alucinación** | Algo que suena bien pero es falso |

## Estado de validación (29-sep-2026)

| Pieza | Estado |
|---|---|
| Parte 1 (9 scripts) | Ejecutados con Python 3.12; salidas como las describen sus README |
| Parte 2 en modo simulado (ejercicios 10–21) | Ejecutados de punta a punta; `pytest`: 20 pruebas OK; `ruff`: sin hallazgos; quality gate del ejercicio 16: pasa |
| Beam (ejercicio 20) | Pipeline ejecutado localmente con Beam 2.76; reconcilia contra SAS |
| ADK (ejercicio 15) | Agentes construidos y herramienta de validación probada con google-adk 2.10; **no ejecutado contra Vertex AI** |
| Terraform (`infra/`) | `terraform fmt` + `validate` OK con provider google 7.46; **no aplicado** a un proyecto real |
| Llamadas reales a Vertex AI, BigQuery, deploys de Functions/Cloud Run, DAG de Composer | **No ejecutados**: este entorno no tiene cuenta de GCP. El código sigue las firmas de google-genai 2.25 y google-cloud-bigquery 3.45 verificadas por introspección; confirma IDs de modelo y precios antes de usar dinero real |
| Imagen Docker (ejercicio 19) | No construida aquí; la app se probó con el `TestClient` de FastAPI |
