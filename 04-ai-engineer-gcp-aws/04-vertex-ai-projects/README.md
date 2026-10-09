# Parte 2 — Desarrollo de IA en Google Cloud

12 micro labs que construyen, pieza por pieza, una **plataforma de migración SAS → Python/GCP
con agentes de IA**: el caso exacto de la vacante de Senior AI Engineer.

**Todo corre en modo simulado por defecto** (gratis, sin cuenta de GCP). Cuando quieras usar la
nube de verdad: [docs/gcp-connect.md](../docs/gcp-connect.md) y `MODO=real` en `.env`.

## Ruta

| # | Lab | Qué construyes | Servicio GCP |
|---|---|---|---|
| 10 | [setup_gcp](10_setup_gcp/) | Checklist del entorno con diagnóstico | Proyecto, IAM, ADC |
| 11 | [gemini_sdk](11_gemini_sdk/) | Primeras llamadas; tokens, costo, latencia | Vertex AI (Gemini) |
| 12 | [salida_estructurada](12_salida_estructurada/) | Extraer reglas de negocio de SAS como JSON validado | Vertex AI |
| 13 | [embeddings_rag](13_embeddings_rag/) | RAG sobre equivalencias SAS↔Python | Vertex AI embeddings |
| 14 | [agente_herramientas](14_agente_herramientas/) | Agente con function calling | Vertex AI |
| 15 | [multi_agente](15_multi_agente/) | **Analista → Convertidor ⇄ Validador → Documentador** (+ versión ADK) | Vertex AI, ADK |
| 16 | [evaluacion](16_evaluacion/) | Golden set, LLM como juez, quality gate en CI | — |
| 17 | [bigquery](17_bigquery/) | SAS → BigQuery SQL, dry run, `VECTOR_SEARCH` | BigQuery + Terraform |
| 18 | [cloud_functions_storage](18_cloud_functions_storage/) | Análisis automático al subir un `.sas` | Storage, Functions, Eventarc |
| 19 | [cloud_run_api](19_cloud_run_api/) | API REST del migrador en contenedor | Cloud Run |
| 20 | [composer_dataflow](20_composer_dataflow/) | Pipeline Beam + DAG de Airflow | Dataflow, Composer |
| 21 | [monitoreo_gobernanza](21_monitoreo_gobernanza/) | Costos, logs, auditoría, guardrails | Logging, BigQuery |

Cada carpeta tiene `README.md` (concepto + preguntas de entrevista) e `INSTRUCCIONES.md`
(paso a paso, qué observar, **qué hacer si algo falla**, retos).

## Estructura

```
04-vertex-ai-projects/
├── comun/               código compartido: el ÚNICO lugar que habla con Vertex AI
│   ├── config.py          .env -> configuración (MODO simulado/real)
│   ├── llm.py             generar(), embeber(), SesionAgente
│   ├── simulado.py        respuestas falsas para aprender gratis
│   ├── esquemas.py        modelos Pydantic de las respuestas
│   ├── agentes.py         analista, convertidor, documentador
│   ├── orquestador.py     flujo multi-agente con autocorrección
│   ├── validacion.py      ejecutar + reconciliar contra SAS
│   ├── guardrails.py      redacción de datos sensibles, revisión de código
│   ├── observabilidad.py  logs JSON + registro de costo por llamada
│   ├── precios.py         USD por millón de tokens
│   ├── sas/               3 programas SAS de ejemplo
│   └── datos/             ventas.csv + salida esperada de SAS (golden)
├── 10_... 21_...        los micro labs
├── tests/               pytest (siempre en simulado)
├── requirements.txt     versiones fijadas
└── .env.example         configuración documentada
```

## Arranque rápido

```bash
cd 04-vertex-ai-projects
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
python 10_setup_gcp/verificar_entorno.py
python 15_multi_agente/migrar.py
pytest
```

Todo lo que se puede probar y cómo: [docs/testing-on-gcp.md](../docs/testing-on-gcp.md).
