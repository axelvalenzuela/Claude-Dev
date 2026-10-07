# Micro lab 01: API serverless (API Gateway REST + Lambda + DynamoDB + Cognito + WAF)

> **Objetivo:** desplegar una API REST definida por **contrato OpenAPI**, con defensa en profundidad (WAF, API key, JWT de Cognito, validación de esquema) y observabilidad (access logs, X-Ray, alarmas).

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~2 min · **Costo si queda encendido:** Free tier (+ WAF ~USD 6/mes)

**Prerrequisitos**

- Lab 00 desplegado (`TF_STATE_BUCKET`)

**1. Prepara las variables**

```bash
cd 03-cloud-e-infraestructura/lab10-terraform-aws
cp microlabs/01-serverless-apigw-lambda-dynamodb/terraform.tfvars.example microlabs/01-serverless-apigw-lambda-dynamodb/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `owner` | tu correo |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  01-serverless-apigw-lambda-dynamodb
bash scripts/lab.sh plan  01-serverless-apigw-lambda-dynamodb   # revisa qué se crea
bash scripts/lab.sh apply 01-serverless-apigw-lambda-dynamodb
```

**3. Después del apply**

- Opcional para el lab 07: `enable_fault_injection = true`

**4. Verifica**

```bash
bash scripts/lab.sh test 01-serverless-apigw-lambda-dynamodb   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 01-serverless-apigw-lambda-dynamodb
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| openapi.yaml.tpl → `paths` | Agregar rutas/métodos; cada uno con `x-amazon-apigateway-integration` | Para nuevas operaciones del API |
| openapi.yaml.tpl → `components.schemas.Item` | Campos, tipos, límites (validación en el borde) | Cuando cambie el modelo de datos |
| src/items/app.py | Lógica de negocio y llaves `pk/sk` de DynamoDB | Siempre que cambie el dominio |
| main.tf → `aws_wafv2_web_acl` | Reglas administradas y `waf_rate_limit_per_5min` | Si el WAF bloquea tráfico legítimo |
| main.tf → `aws_cognito_user_pool` | Password policy, MFA (`OPTIONAL`/`ON`) | Requisitos de seguridad |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
Cliente ──HTTPS──► AWS WAF (Common, BadInputs, rate-limit/IP)
                     │
                     ▼
            API Gateway REST (REGIONAL, stage v1)
            ├─ Usage plan + API key (throttle + cuota mensual)
            ├─ Cognito User Pool authorizer (JWT)
            ├─ Request validator (esquema OpenAPI)
            ├─ /health → MOCK
            └─ /items, /items/{id} → Lambda proxy
                                      │
                                      ▼
                          Lambda items (arm64, X-Ray, concurrencia 20)
                                      │  IAM: solo Get/Put/Delete/Query
                                      ▼
                          DynamoDB items (on-demand, PITR, SSE)
                          pk = USER#<sub>, sk = ITEM#<uuid>  (aislamiento por usuario)
```

## Archivos

| Archivo | Contenido |
|---|---|
| `openapi.yaml.tpl` | **Template del contrato**: rutas, esquemas, seguridad, integraciones `x-amazon-apigateway-*` |
| `main.tf` | Tabla, Lambda, Cognito, API, stage, usage plan, WAF, alarmas |
| `src/items/app.py` | Handler CRUD |
| `terraform.tfvars.example` | Parámetros |

## Parámetros

| Variable | Default | Descripción |
|---|---|---|
| `stage_name` | `v1` | Stage de despliegue (versionado de API) |
| `throttle_rate_limit` / `throttle_burst_limit` | 50 / 100 | Límite de RPS del stage y del usage plan |
| `monthly_quota` | 100000 | Solicitudes/mes por API key |
| `enable_waf` | `true` | Asocia Web ACL al stage |
| `waf_rate_limit_per_5min` | 1000 | Bloqueo por IP |
| `log_retention_days` | 30 | Retención de logs |

## Pasos

```bash
cd 03-cloud-e-infraestructura/lab10-terraform-aws/microlabs/01-serverless-apigw-lambda-dynamodb
cp terraform.tfvars.example terraform.tfvars
terraform init -backend-config="bucket=<TF_STATE_BUCKET>" -backend-config="key=03-cloud-e-infraestructura/lab10-terraform-aws/01-serverless-apigw-lambda-dynamodb/dev.tfstate" \
               -backend-config="region=us-east-1" -backend-config="use_lockfile=true" -backend-config="encrypt=true"
terraform plan -out tfplan && terraform apply tfplan
```

## Pruebas

```bash
API=$(terraform output -raw api_url)
POOL=$(terraform output -raw user_pool_id); CLIENT=$(terraform output -raw user_pool_client_id)
KEY=$(aws apigateway get-api-key --api-key $(terraform output -raw api_key_id) --include-value --query value --output text)

# 1. Crear usuario de prueba
aws cognito-idp admin-create-user --user-pool-id $POOL --username alumno@example.com --message-action SUPPRESS
aws cognito-idp admin-set-user-password --user-pool-id $POOL --username alumno@example.com --password 'Lab10-Passw0rd!' --permanent
TOKEN=$(aws cognito-idp initiate-auth --client-id $CLIENT --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=alumno@example.com,PASSWORD='Lab10-Passw0rd!' --query AuthenticationResult.IdToken --output text)

# 2. Llamadas
curl $API/health
curl -X POST $API/items -H "Authorization: $TOKEN" -H "x-api-key: $KEY" -H 'Content-Type: application/json' -d '{"name":"laptop","price":999}'
curl $API/items -H "Authorization: $TOKEN" -H "x-api-key: $KEY"
curl -X POST $API/items -H "Authorization: $TOKEN" -H "x-api-key: $KEY" -d '{"foo":1}'   # 400 por validación
curl $API/items                                                                             # 401/403 sin credenciales
```

## Parámetros en GitLab

| Variable | Tipo | Ejemplo |
|---|---|---|
| `LAB01_TFVARS` | File | contenido de `terraform.tfvars` |
| `TF_VAR_owner` | Variable | `equipo@dominio.com` (alternativa a tfvars) |

<!-- detalle-funcional -->
## Ejecución rápida

```bash
cd 03-cloud-e-infraestructura/lab10-terraform-aws
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/01-serverless-apigw-lambda-dynamodb/terraform.tfvars.example microlabs/01-serverless-apigw-lambda-dynamodb/terraform.tfvars   # edita owner y demás
bash scripts/lab.sh init  01-serverless-apigw-lambda-dynamodb
bash scripts/lab.sh apply 01-serverless-apigw-lambda-dynamodb
bash scripts/lab.sh test  01-serverless-apigw-lambda-dynamodb      # smoke test automatizado (abajo)
bash scripts/lab.sh destroy 01-serverless-apigw-lambda-dynamodb
```

Con `make`: `make apply LAB=01-serverless-apigw-lambda-dynamodb` · `make test LAB=01-serverless-apigw-lambda-dynamodb`. Requisitos del smoke test: AWS CLI v2, `jq`, `curl` y credenciales con permisos de escritura sobre el lab.

## Prueba automatizada (`scripts/smoke-test.sh`)

Crea un usuario temporal en Cognito y valida: `/health` 200 sin auth, 401 sin JWT, 403 sin API key, 400 por validación OpenAPI, CRUD completo (201 → 200 → 204 → 404), ráfaga contra el usage plan, access logs y trazas X-Ray. El usuario se borra al terminar.

**Inyección de fallas (para el lab 07):** con `enable_fault_injection = true`, cualquier request con el header `x-fault-injection: 1` hace fallar la Lambda (HTTP 502). Está desactivada por defecto y nunca debe activarse en producción.

### Resultado esperado (extracto)

```
== Endpoints
  OK   GET /health (MOCK, sin auth) (200)
  OK   GET /items sin credenciales (401)
  OK   GET /items con JWT pero sin API key (403)
  OK   POST /items con cuerpo inválido (validación OpenAPI) (400)
  OK   POST /items crea el item (3f1c...)
  OK   GET /items devuelve el item (1)
  OK   DELETE /items/{id} (204)
  OK   GET /items/{id} después de borrar (404)
SMOKE TEST OK  (13 verificaciones)
```

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `CloudWatch Logs role ARN must be set in account settings` | `aws_api_gateway_account` es un ajuste por región y cuenta; si otro stack lo administra, elimina ese recurso del lab y reutiliza el rol existente. |
| 403 `Forbidden` aun con API key | La key tarda unos segundos en asociarse al usage plan después del apply. Reintenta; verifica con `aws apigateway get-usage-plan-keys`. |
| 401 con token válido | Usa el **IdToken** (no el AccessToken): el authorizer de Cognito en REST API valida el `aud` del IdToken. |
| WAF bloquea tus pruebas (403 con `wafStatus` BLOCK) | Superaste `waf_rate_limit_per_5min` desde tu IP; espera 5 min o sube el límite. |
<!-- detalle-funcional -->

## Well-Architected

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Contrato OpenAPI versionado; redeploy automático por hash; logs JSON |
| Seguridad | WAF + API key + Cognito (MFA opcional, password policy) + validación + IAM por tabla; aislamiento por `sub` |
| Confiabilidad | Servicios multi-AZ gestionados; throttling; concurrencia reservada; PITR |
| Eficiencia de rendimiento | Lambda arm64; DynamoDB single-digit ms; integración MOCK sin cómputo |
| Optimización de costos | Pago por uso; cuotas por cliente; retención de logs acotada |
| Sostenibilidad | Cero cómputo ocioso; Graviton |

## Storage mínimo

| Recurso | Definición |
|---|---|
| DynamoDB | On-demand, sin capacidad provisionada; PITR on |
| CloudWatch Logs | Access + Lambda, 30 días |
| Lambda | Paquete < 1 MB, 256 MB RAM |

**Costo aproximado del lab:** WAF ~USD 5 por Web ACL al mes + USD 1 por regla; el resto queda prácticamente dentro del free tier.

## Retos

1. Cambia a **HTTP API (v2)** con JWT authorizer y compara costo y latencia.
2. Agrega un **canary deployment** en el stage (`canary_settings`).
3. Sustituye la API key por un **Lambda authorizer** con caché.

## Limpieza

`terraform destroy`
