# Micro lab 08 (GCP): Analítica con BigQuery: ingesta streaming, capas de datos y vista autorizada

> **Objetivo:** Plataforma de datos mínima: ingesta sin código desde Pub/Sub, tabla particionada y clusterizada con filtro de partición obligatorio, MERGE programado y acceso de analistas solo a vistas sin PII.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y micro lab 00).

**Tiempo de apply:** ~2 min · **Costo si queda encendido:** Free tier

**Prerrequisitos**

- Micro lab 00

**1. Prepara las variables**

```bash
cd 06-terraform-gcp
cp microlabs/08-data-bigquery-analytics/terraform.tfvars.example microlabs/08-data-bigquery-analytics/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `analyst_members` | opcional |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del micro lab 00>
bash scripts/lab.sh init  08-data-bigquery-analytics
bash scripts/lab.sh plan  08-data-bigquery-analytics   # revisa qué se crea
bash scripts/lab.sh apply 08-data-bigquery-analytics
```

**3. Después del apply**

- Consulta: `bq query --use_legacy_sql=false 'SELECT * FROM <shared_view>'`

**4. Verifica**

```bash
bash scripts/lab.sh test 08-data-bigquery-analytics   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 08-data-bigquery-analytics
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| schemas/events.json | Columnas de la tabla cruda | Nuevos eventos |
| sql/merge_daily_kpis.sql.tpl | KPIs calculados | Nuevas métricas |
| main.tf → `google_bigquery_table.v_kpis.view.query` | Qué ven los analistas | Siempre sin PII |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
Productores ─► topic events ─► BigQuery subscription (use_table_schema, drop_unknown_fields)
                                   │ inválidos (5 intentos) ─► topic ingest-dlq
                                   ▼
dataset _raw   : events (partición DAY por event_ts, cluster country+event_type, require_partition_filter,
                 expiración de particiones 90 d) — incluye PII (email)
     │ Scheduled query diaria (Data Transfer Service, SA dedicada): MERGE idempotente
     ▼
dataset _curated: daily_kpis (day, country, event_type, events, unique_users, revenue)
     │ vista AUTORIZADA (el dataset curated autoriza la vista; los analistas no leen curated)
     ▼
dataset _shared : v_kpis (sin user_id ni email) ◄── analistas: dataViewer + jobUser
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `google_bigquery_dataset` x3 | Capas raw / curated / shared |
| `google_bigquery_table.events` + `schemas/events.json` | Particionado, clustering, filtro de partición obligatorio |
| `google_pubsub_subscription.to_bigquery` | Ingesta directa con DLQ |
| `google_bigquery_data_transfer_config` + `sql/merge_daily_kpis.sql.tpl` | Scheduled query con SA propia |
| `google_bigquery_dataset_access.authorized_view` | Patrón de vista autorizada |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `bq_location` | US |  |
| `raw_retention_days` | 90 | Expiración de particiones |
| `kpi_schedule` | every day 06:00 | Sintaxis de Data Transfer |
| `analyst_members` | `[]` | Acceso solo a shared |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd 06-terraform-gcp
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del micro lab 00>   # no aplica al micro lab 00
cp microlabs/08-data-bigquery-analytics/terraform.tfvars.example microlabs/08-data-bigquery-analytics/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  08-data-bigquery-analytics
bash scripts/lab.sh apply 08-data-bigquery-analytics
bash scripts/lab.sh test  08-data-bigquery-analytics
bash scripts/lab.sh destroy 08-data-bigquery-analytics
```

Revisa el costo antes de consultar: `bq query --dry_run ...` muestra los bytes que se escanearían.

## Prueba automatizada (`scripts/smoke-test.sh`)

31 mensajes (1 inválido); 30 filas en raw; **consulta sin filtro de partición rechazada**; dry run con partición + cluster; mensaje inválido en la DLQ; ejecución del scheduled query y KPIs del día; la vista expone **solo** columnas agregadas.

### Resultado esperado (extracto)

```
== Ingesta streaming (Pub/Sub -> BigQuery)
  OK   30 filas de la corrida
== Control de costo
  OK   Consulta sin filtro de partición rechazada (require_partition_filter)
== Mensaje inválido -> dead letter
  OK   Mensaje fuera de esquema en la DLQ
== Vista autorizada (sin PII)
  OK   Columnas expuestas (day,country,event_type,events,unique_users,revenue)
SMOKE TEST OK  (7 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `GCP08_TFVARS` | File | terraform.tfvars |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| La suscripción BigQuery no escribe | El agente de Pub/Sub necesita `bigquery.dataEditor` en el dataset raw (incluido). |
| Scheduled query falla con permisos | La SA del transfer necesita jobUser + dataViewer (raw) + dataEditor (curated); el usuario que crea el transfer debe poder `actAs` esa SA. |
| La vista falla para analistas | Falta `google_bigquery_dataset_access` (vista autorizada) o el analista no tiene `jobUser`. |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | SQL versionado; MERGE idempotente |
| Seguridad | Capas, vista autorizada, PII fuera del dataset compartido |
| Confiabilidad | DLQ en la ingesta |
| Rendimiento | Partición + clustering |
| Costos | `require_partition_filter`, expiración, dry run |
| Sostenibilidad | Menos bytes escaneados |

## Storage mínimo

| Recurso | Definición |
|---|---|
| BigQuery raw | Particiones expiran a los 90 días |
| BigQuery curated | KPIs agregados (KB por día) |

**Costo aproximado:** Free tier: 10 GB de storage y 1 TB de consultas al mes.
