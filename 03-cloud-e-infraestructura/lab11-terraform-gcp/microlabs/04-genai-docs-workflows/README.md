# Micro lab 04 (GCP): Pipeline de IA para documentos con Cloud Workflows (sin funciones propias)

> **Objetivo:** Orquestar APIs de IA administradas con **conectores de Workflows**: OCR, entidades y resumen con Gemini, en paralelo y con manejo de errores, guardando en BigQuery.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~4 min · **Costo si queda encendido:** Por uso

**Prerrequisitos**

- Lab 00

**1. Prepara las variables**

```bash
cd 03-cloud-e-infraestructura/lab11-terraform-gcp
cp microlabs/04-genai-docs-workflows/terraform.tfvars.example microlabs/04-genai-docs-workflows/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `vertex_location` | región con Gemini (us-central1) |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  04-genai-docs-workflows
bash scripts/lab.sh plan  04-genai-docs-workflows   # revisa qué se crea
bash scripts/lab.sh apply 04-genai-docs-workflows
```

**3. Después del apply**

- `gcloud storage cp samples/comunicado.txt gs://<bucket>/incoming/`

**4. Verifica**

```bash
bash scripts/lab.sh test 04-genai-docs-workflows   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 04-genai-docs-workflows
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| workflow.yaml → `route` | Extensiones soportadas y su procesamiento | Nuevos formatos (PDF con Document AI) |
| workflow.yaml → rama `summary_branch` | Prompt y `generationConfig` | Otro tipo de análisis (clasificar, traducir) |
| main.tf → `google_bigquery_table.documents` | Columnas de resultados | Si guardas más campos |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
Usuario ──gcloud storage cp──► gs://...-docs/incoming/*   (expira a 30 días)
                                  │ Eventarc: google.cloud.storage.object.v1.finalized
                                  ▼
                       Cloud Workflows pipeline (SA con mínimo privilegio, logs solo de errores)
     route por extensión ─► .txt: http.get (OAuth2)   ·   .png/.jpg: Vision TEXT_DETECTION   ·   otro: raise
                                  ▼
             parallel ┬─ Natural Language analyzeEntities
                      └─ Vertex AI generateContent (Gemini) → resumen
                                  ▼
             BigQuery insertAll (documents, partición diaria)  ·  except → log ERROR → FAILED → alerta
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `workflow.yaml` | Definición: rutas, `parallel` con variables `shared`, `try/except`, conectores `googleapis.*` |
| `google_workflows_workflow` | `user_env_vars` (modelo, dataset, idioma) y `call_log_level = LOG_ERRORS_ONLY` |
| `google_eventarc_trigger` | Filtro por tipo de evento y bucket; SA con `workflows.invoker` |
| `google_bigquery_table.documents` | Columna `entities` de tipo JSON |
| `google_monitoring_alert_policy.failed` | `finished_execution_count{status=FAILED}` > 0 |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `model` | `gemini-2.5-flash` |  |
| `vertex_location` | `us-central1` | El conector no admite `global` |
| `language` | `es` | Natural Language |
| `document_retention_days` | 30 | Minimización de datos |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd 03-cloud-e-infraestructura/lab11-terraform-gcp
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/04-genai-docs-workflows/terraform.tfvars.example microlabs/04-genai-docs-workflows/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  04-genai-docs-workflows
bash scripts/lab.sh apply 04-genai-docs-workflows
bash scripts/lab.sh test  04-genai-docs-workflows
bash scripts/lab.sh destroy 04-genai-docs-workflows
```

Puedes abrir el workflow en la consola para ver cada paso de una ejecución (entradas y salidas por step).

## Prueba automatizada (`scripts/smoke-test.sh`)

Sube `samples/comunicado.txt` → ejecución **SUCCEEDED** → fila en BigQuery con resumen y entidades UABC / LOCATION / PERSON; un `.docx` → **FAILED**; un archivo fuera de `incoming/` → el workflow lo **ignora** (sin fila).

### Resultado esperado (extracto)

```
== Documento .txt
  OK   Ejecución (SUCCEEDED)
  OK   Resumen de Gemini: - La UABC y Google Cloud anunciaron un programa...
  OK   Entidad ORGANIZATION (UABC)
== Formato no soportado -> FAILED
  OK   Ejecución (FAILED)
== Fuera de incoming/ -> el workflow lo ignora
  OK   Sin fila en BigQuery para otros/ (0)
SMOKE TEST OK  (8 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `LAB04_TFVARS` | File | terraform.tfvars |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| El trigger no dispara | El agente de Cloud Storage necesita `roles/pubsub.publisher` (incluido); el trigger tarda ~2 min en activarse. |
| `PERMISSION_DENIED` en Vision/Language | Falta `serviceusage.serviceUsageConsumer` en la SA del workflow o la API no está habilitada. |
| Error del conector de Vertex | Usa una región en `vertex_location` (p. ej. `us-central1`) y un modelo disponible allí. |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Historial visual de ejecuciones por paso |
| Seguridad | SA mínima; sin contenido en logs; bucket privado |
| Confiabilidad | try/except; alerta de fallas; reintentos de conectores |
| Rendimiento | Entidades y resumen en paralelo |
| Costos | Sin funciones ni servidores; pago por paso |
| Sostenibilidad | Datos expiran |

## Storage mínimo

| Recurso | Definición |
|---|---|
| GCS | STANDARD con expiración de 30 días |
| BigQuery | 1 fila por documento, partición diaria |

**Costo aproximado:** Workflows: 5,000 pasos internos gratis/mes; APIs de IA por uso.
