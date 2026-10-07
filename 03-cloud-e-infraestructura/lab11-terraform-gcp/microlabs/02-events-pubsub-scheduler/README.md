# Micro lab 02 (GCP): Arquitectura orientada a eventos con Pub/Sub (schema, push OIDC, DLQ, filtros, BigQuery)

> **Objetivo:** Desacoplar productores y consumidores: contrato AVRO validado al publicar, push autenticado con reintentos y dead letter, filtros por atributos, auditoría sin código en BigQuery y tareas con Cloud Scheduler.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~6 min · **Costo si queda encendido:** Free tier

**Prerrequisitos**

- Lab 00

**1. Prepara las variables**

```bash
cd 03-cloud-e-infraestructura/lab11-terraform-gcp
cp microlabs/02-events-pubsub-scheduler/terraform.tfvars.example microlabs/02-events-pubsub-scheduler/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `build_service_account` | output del lab 00 |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  02-events-pubsub-scheduler
bash scripts/lab.sh plan  02-events-pubsub-scheduler   # revisa qué se crea
bash scripts/lab.sh apply 02-events-pubsub-scheduler
```

**3. Después del apply**

- Publica a mano: `gcloud pubsub topics publish <topic> --message='{...}' --attribute=tier=high`

**4. Verifica**

```bash
bash scripts/lab.sh test 02-events-pubsub-scheduler   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 02-events-pubsub-scheduler
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| schemas/order.avsc | Contrato del evento (AVRO) | Cambios de evento (versiona el schema) |
| main.tf → `filter` de las suscripciones | Filtros por atributos | Nuevos consumidores |
| main.tf → `retry_policy`, `dead_letter_policy` | Reintentos y DLQ | Según SLA del consumidor |
| src/processor/main.py | Procesamiento idempotente | Lógica |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
Productores ──publish (JSON validado por schema AVRO)──► topic orders (retención 7 d → seek/replay)
       ├─► sub processor-push ──OIDC (SA push)──► function processor ── 500 ⇒ retry 10–60 s
       │        └─ 5 intentos ─► topic dead-letter ─► sub dead-letter-inspect  + alerta
       ├─► sub high-value  (filter attributes.tier = "high")      → consumidor pull
       └─► sub audit-bq    (BigQuery subscription, write_metadata) → tabla order_events (partición diaria)
Cloud Scheduler (cron 0 * * * *, OIDC) ─► function reporter
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `google_pubsub_schema` + `schemas/order.avsc` | Contrato del evento; mensajes inválidos se rechazan al publicar |
| `google_pubsub_subscription.processor` | Push con `oidc_token`, `retry_policy`, `dead_letter_policy` |
| `google_pubsub_subscription.high_value` | Filtro por atributos (sin código) |
| `google_pubsub_subscription.audit` + BigQuery | Ingesta directa a tabla particionada |
| `google_cloud_scheduler_job.report` | HTTP + OIDC hacia la función reporter |
| IAM del agente de Pub/Sub | publisher en la DLQ, subscriber en la sub, tokenCreator sobre el SA push |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `max_delivery_attempts` | 5 | Antes de la DLQ (5-100) |
| `audit_retention_days` | 30 | Expiración de la tabla |
| `report_schedule` / `schedule_timezone` | `0 * * * *` / Tijuana |  |
| `notification_channels` | `[]` | Canales de Monitoring |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd 03-cloud-e-infraestructura/lab11-terraform-gcp
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/02-events-pubsub-scheduler/terraform.tfvars.example microlabs/02-events-pubsub-scheduler/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  02-events-pubsub-scheduler
bash scripts/lab.sh apply 02-events-pubsub-scheduler
bash scripts/lab.sh test  02-events-pubsub-scheduler
bash scripts/lab.sh destroy 02-events-pubsub-scheduler
```

En el encoding JSON de AVRO las uniones se publican como `{"double": 250}`; ver `scripts/smoke-test.sh`. Replay: `gcloud pubsub subscriptions seek <sub> --time=<RFC3339>`.

## Prueba automatizada (`scripts/smoke-test.sh`)

Mensaje sin `orderId` **rechazado por el schema**; 3 órdenes publicadas; logs de la función con la orden normal; la suscripción filtrada recibe **solo** la de `tier=high`; la orden sin `amount` llega a la **DLQ** tras 5 intentos; 3 filas en BigQuery; ejecución manual del Scheduler.

### Resultado esperado (extracto)

```
== Schema AVRO (validación al publicar)
  OK   Mensaje sin orderId rechazado por el schema
== Filtro por atributos
  OK   Suscripción high-value recibió solo la orden tier=high (smoke...-high)
== Dead letter (5 intentos con backoff, ~2-4 min)
  OK   Orden fallida en la DLQ tras 5 intentos
== Auditoría en BigQuery (suscripción directa, sin código)
  OK   3 eventos de la corrida en proyecto.lab11_dev_evt_audit.order_events
SMOKE TEST OK  (10 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `LAB02_TFVARS` | File | terraform.tfvars |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| Nada llega a la DLQ | El agente `service-<num>@gcp-sa-pubsub` necesita publisher en el topic DLQ y subscriber en la sub origen (incluidos en el lab). |
| Push devuelve 401/403 | La audiencia del `oidc_token` debe ser la URL de la función y el SA push debe tener `run.invoker`. |
| La suscripción BigQuery queda en error | El esquema de la tabla debe incluir las columnas de metadata cuando `write_metadata = true`. |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Schema versionado; replay con seek; alerta de DLQ |
| Seguridad | Push con OIDC; funciones privadas |
| Confiabilidad | Retry con backoff + DLQ; consumidores idempotentes |
| Rendimiento | Filtrado en el broker |
| Costos | Auditoría sin cómputo; Scheduler a USD 0.10/job |
| Sostenibilidad | Procesamiento solo con eventos |

## Storage mínimo

| Recurso | Definición |
|---|---|
| Pub/Sub | Retención 7 días (topic) y 14 días (DLQ) |
| BigQuery | Partición diaria con expiración de 30 días |

**Costo aproximado:** Free tier (10 GB/mes de Pub/Sub; Scheduler 3 jobs gratis).
