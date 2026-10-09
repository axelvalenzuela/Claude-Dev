# Micro lab 13 (GCP · GenAI): RAG administrado: Vertex AI Search + grounding de Gemini

> **Objetivo:** Usar el **RAG administrado de Google** (Vertex AI Search / AI Applications): parsing por layout, chunking, ranking, resúmenes con citas y **grounding** de Gemini con `grounding_metadata`. Compáralo con el micro lab 12 para decidir *build vs buy*.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y micro lab 00).

**Tiempo de apply:** ~4 min + indexación · **Costo si queda encendido:** Por consulta (Enterprise + LLM add-on)

**Prerrequisitos**

- Micro lab 00 (`build_service_account`)
- Aceptar los términos de AI Applications en la consola la primera vez

**1. Prepara las variables**

```bash
cd 06-terraform-gcp
cp microlabs/13-genai-vertex-ai-search-grounding/terraform.tfvars.example microlabs/13-genai-vertex-ai-search-grounding/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `invoker_members` | `["user:tu@correo"]` |
| `build_service_account` | output del micro lab 00 |
| `search_location` | `global`, `us` o `eu` |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del micro lab 00>
bash scripts/lab.sh init  13-genai-vertex-ai-search-grounding
bash scripts/lab.sh plan  13-genai-vertex-ai-search-grounding   # revisa qué se crea
bash scripts/lab.sh apply 13-genai-vertex-ai-search-grounding
```

**3. Después del apply**

- Importa los documentos: `bash microlabs/13-genai-vertex-ai-search-grounding/scripts/import-docs.sh --wait` (5-15 min la primera vez)
- Prueba los dos modos: `{"question":"...","mode":"gemini"}` y `{"mode":"search"}`

**4. Verifica**

```bash
bash scripts/lab.sh test 13-genai-vertex-ai-search-grounding   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 13-genai-vertex-ai-search-grounding
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| data/*.txt (o PDF/HTML/DOCX en el bucket) | Documentos indexados | Siempre |
| main.tf → `document_processing_config` | Parser (layout/OCR) y `chunk_size` | Documentos complejos |
| main.tf → `search_engine_config` | Tier y add-ons LLM | Costo vs funcionalidad |
| src/answer/main.py → `system_instruction`, `summary_spec` | Estilo de respuesta y citas | Siempre |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
GCS docs/*.txt (también PDF, HTML, DOCX) ──documents:import──► Data store (layout parser + chunking 500 tokens)
                                                                      │
                                                     Search engine (SEARCH_TIER_ENTERPRISE + SEARCH_ADD_ON_LLM)
Usuario ──ID token──► Cloud Run function answer
  mode=gemini: Gemini + Tool(Retrieval(VertexAISearch(datastore))) → answer + grounding_metadata (chunks, supports)
  mode=search: SearchService.search(summary_spec con citas) → resumen del motor + documentos
```

## Conceptos clave (nivel senior)

| Concepto | Lo que debes saber explicar |
|---|---|
| Grounding | Anclar la respuesta del modelo a fuentes verificables. `grounding_metadata` trae los chunks usados y qué parte de la respuesta respalda cada uno (`grounding_supports`). |
| Grounding con Google Search vs datos propios | `types.Tool(google_search=...)` para información pública reciente; `Retrieval(VertexAISearch)` para datos privados. |
| Layout parser | Entiende títulos, tablas y listas; mejora el chunking frente a cortar texto plano. |
| Build vs buy | Micro lab 12: control total y costo bajo pero tú mantienes chunking, ranking y evaluación. Micro lab 13: calidad empresarial, conectores y citas listos, costo por consulta. |
| Data store vs engine | El data store guarda e indexa; el engine (app) define el tier, los add-ons y lo que consultas. |
| Residencia de datos | `search_location` = `us`/`eu` mantiene índices y procesamiento en esa región. |

## Recursos de Terraform y código

| Recurso / archivo | Propósito |
|---|---|
| `google_discovery_engine_data_store.docs` | Contenido no estructurado con `document_processing_config` |
| `google_discovery_engine_search_engine.docs` | Tier Enterprise + LLM add-on |
| `google_storage_bucket_object.docs` | Sube `data/*.txt` al bucket |
| `scripts/import-docs.sh` | REST `documents:import` (INCREMENTAL) y espera de la operación |
| `src/answer/main.py` | Modos gemini (grounding) y search (resumen con citas) |

## Comandos útiles

```bash
bash scripts/import-docs.sh --wait
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" https://discoveryengine.googleapis.com/v1/projects/<p>/locations/global/collections/default_collection/dataStores/<ds>/branches/default_branch/documents
gcloud services list --enabled | grep discoveryengine
```

## Prueba automatizada (`scripts/smoke-test.sh`)

Importa y espera la indexación; modo gemini responde "25 dólares" citando `planes-y-precios`; modo search resume el crédito de 25 % citando `soporte-y-sla`; una pregunta fuera de dominio no recupera fuentes.

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `sources` vacío justo después del apply | La indexación tarda; el smoke test reintenta durante 5 min. |
| `PERMISSION_DENIED` al importar | El agente `gcp-sa-discoveryengine` necesita leer el bucket (incluido); habilita la API y espera unos minutos. |
| `Search add-on not enabled` | El engine debe ser Enterprise con `SEARCH_ADD_ON_LLM` para resúmenes. |

## Costo

Vertex AI Search Enterprise + LLM add-on: se cobra por cada 1,000 consultas; tiene prueba gratuita.
