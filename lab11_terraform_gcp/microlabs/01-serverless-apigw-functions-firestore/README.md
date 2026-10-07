# Micro lab 01 (GCP): API serverless: API Gateway + Cloud Run functions + Firestore

> **Objetivo:** Exponer una API REST con contrato OpenAPI, API keys con cuota, backend **privado** (solo invocable por el gateway) y datos en Firestore con IAM condicionado.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~6 min · **Costo si queda encendido:** Free tier

**Prerrequisitos**

- Lab 00

**1. Prepara las variables**

```bash
cd lab11_terraform_gcp
cp microlabs/01-serverless-apigw-functions-firestore/terraform.tfvars.example microlabs/01-serverless-apigw-functions-firestore/terraform.tfvars
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
bash scripts/lab.sh init  01-serverless-apigw-functions-firestore
bash scripts/lab.sh plan  01-serverless-apigw-functions-firestore   # revisa qué se crea
bash scripts/lab.sh apply 01-serverless-apigw-functions-firestore
```

**3. Después del apply**

- Opcional para el lab 07: `enable_fault_injection = true`
- La API key: `terraform output -raw api_key`

**4. Verifica**

```bash
bash scripts/lab.sh test 01-serverless-apigw-functions-firestore   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 01-serverless-apigw-functions-firestore
```
<!-- despliegue -->


## Arquitectura

```
Cliente ──HTTPS + x-api-key──► API Gateway (OpenAPI 2.0, cuota 120/min por consumidor)
                                   │ ID token del SA lab11-dev-api-gw (x-google-backend)
                                   ▼
                     Cloud Run function items (python313, max 5 instancias)
                     invoker = SOLO el SA del gateway  →  llamada directa = 403
                                   │ SA lab11-dev-api-fn (datastore.user condicionado a 1 base)
                                   ▼
                     Firestore (Native) lab11-dev-api-items · PITR
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `openapi.yaml.tpl` | Contrato: rutas, `securityDefinitions` (api_key), `x-google-backend`, `x-google-management` (cuotas) |
| `google_api_gateway_api / _api_config / _gateway` | Gateway regional; config con `create_before_destroy` (cambios sin caída) |
| `google_apikeys_key` | Key restringida al servicio administrado del API |
| `module.items_fn` | Función gen2 construida desde `src/items` (sin Docker) |
| `google_firestore_database` | Base nombrada con PITR; IAM condition `resource.name.startsWith(...)` |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `quota_per_minute` | 120 | Requests/min por consumidor |
| `max_instances` | 5 | Tope de escalado y costo |
| `enable_fault_injection` | `false` | Header `x-fault-injection` → 500 (para el lab 07) |
| `build_service_account` | `null` | Output del lab 00 |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd lab11_terraform_gcp
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/01-serverless-apigw-functions-firestore/terraform.tfvars.example microlabs/01-serverless-apigw-functions-firestore/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  01-serverless-apigw-functions-firestore
bash scripts/lab.sh apply 01-serverless-apigw-functions-firestore
bash scripts/lab.sh test  01-serverless-apigw-functions-firestore
bash scripts/lab.sh destroy 01-serverless-apigw-functions-firestore
```

La validación del cuerpo se hace en el código (`_validate`): ESPv2 no valida contra el esquema.

## Prueba automatizada (`scripts/smoke-test.sh`)

Gateway listo; `/health` 200 sin key; 401 sin key y 400 con key inválida; **la función directa responde 403** (backend privado); CRUD completo 201 → 200 → 204 → 404; ráfaga que supera la cuota → **429**.

### Resultado esperado (extracto)

```
== Gateway (https://lab11-dev-api-xxxx.uc.gateway.dev)
  OK   GET /items sin API key (401)
== Backend privado
  OK   Función directa sin ID token (403)
== CRUD
  OK   POST cuerpo inválido (validación en código) (400)
  OK   DELETE /items/{id} (204)
== Cuota por API key (120/min)
  OK   Aparece 429 al exceder la cuota
SMOKE TEST OK  (12 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `LAB01_TFVARS` | File | terraform.tfvars |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `API_KEY_SERVICE_BLOCKED` / 403 con key válida | El servicio administrado del API tarda en habilitarse; espera 1-2 min tras el apply. |
| Build de la función falla con permisos | Pasa `build_service_account` del lab 00 o da `roles/cloudbuild.builds.builder` a la SA de compute por defecto. |
| `Database '(default)' not found` | La función usa la base nombrada de `FIRESTORE_DATABASE`; no requiere la base `(default)`. |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Contrato versionado; logs JSON con trace |
| Seguridad | API key + cuota + backend privado + IAM condicionado |
| Confiabilidad | Servicios regionales administrados; PITR en Firestore |
| Rendimiento | Escala a cero y hasta 5 instancias |
| Costos | Pago por uso; cuotas por consumidor |
| Sostenibilidad | Sin cómputo ocioso |

## Storage mínimo

| Recurso | Definición |
|---|---|
| Firestore | Pago por documento/operación; PITR 7 días |
| GCS código | Zips con expiración de 30 días |

**Costo aproximado:** Free tier cubre el lab (API Gateway 2 M llamadas/mes; Functions 2 M invocaciones).
