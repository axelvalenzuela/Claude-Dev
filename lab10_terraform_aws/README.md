# Lab 10: Micro labs de AWS con Terraform (SRE, serverless, IA y gobernanza)

Colección de 12 micro labs **independientes y modulares** para aprender a desplegar servicios de AWS con Terraform, alineados con el **AWS Well-Architected Framework** y desplegados por GitOps desde **GitLab CI** con OIDC (sin llaves de acceso).

> 📄 Los diagramas de arquitectura, las tablas de implementación y la guía de RBAC y seguridad DevOps están en [docs/lab10-arquitecturas.pdf](docs/lab10-arquitecturas.pdf).

## Empieza aquí

| Si quieres... | Ve a |
|---|---|
| Instalar todo y desplegar desde cero | [DESPLIEGUE.md](DESPLIEGUE.md) |
| Practicar el SDK de IA (boto3 + Bedrock) en scripts cortos | [sdk-examples/](sdk-examples/) |
| Ver la arquitectura de cada micro lab | [docs/lab10-arquitecturas.pdf](docs/lab10-arquitecturas.pdf) |
| Comparar con Google Cloud | [GUIA-AWS-GCP.md](../lab11_terraform_gcp/docs/GUIA-AWS-GCP.md) |

Cada carpeta de micro lab se llama `NN-categoria-servicios` (por ejemplo `04-genai-chatbot-bedrock`) y su README empieza con **"Despliegue paso a paso"**.

## Índice

| # | Micro lab | Servicios | Tipo de arquitectura | Costo si queda encendido |
|---|---|---|---|---|
| 00 | [bootstrap](microlabs/00-platform-bootstrap-s3-oidc) | S3 state, KMS, IAM OIDC, Budgets | Plataforma | ~USD 1/mes |
| 01 | [serverless-api](microlabs/01-serverless-apigw-lambda-dynamodb) | API Gateway REST, Lambda, DynamoDB, Cognito, WAF | Serverless | ~USD 6/mes (WAF) |
| 02 | [appsync-graphql](microlabs/02-serverless-appsync-graphql) | AppSync, resolvers JS, DynamoDB, Cognito | Serverless GraphQL | Pago por uso |
| 03 | [eventbridge-event-driven](microlabs/03-events-eventbridge-sqs) | EventBridge bus/archive/Scheduler, SQS, Lambda | Event-driven | Pago por uso |
| 04 | [chatbot-bedrock](microlabs/04-genai-chatbot-bedrock) | HTTP API, Lambda, Bedrock Converse, Guardrails | IA generativa | Por token |
| 05 | [ai-document-pipeline](microlabs/05-genai-docs-stepfunctions) | S3, Step Functions, Textract, Comprehend, Bedrock | IA orquestada | Pago por uso |
| 06 | [three-tier-web](microlabs/06-web3tier-alb-asg-rds) | VPC, ALB, WAF, ASG, RDS Multi-AZ | 3 niveles | ~USD 95/mes ⚠️ |
| 07 | [sre-observability](microlabs/07-sre-slo-cloudwatch-fis) | CloudWatch SLO/burn rate, Synthetics, Chatbot, FIS | SRE | ~USD 10/mes |
| 08 | [neptune-graph](microlabs/08-data-neptune-graph) | Neptune Serverless, Lambda VPC, S3 loader | Grafos | ~USD 115/mes ⚠️ |
| 09 | [mgn-migration](microlabs/09-migration-mgn) | AWS MGN, VPC staging, KMS, IAM | Migración rehost | Según los servidores |
| 10 | [cloudformation-stacksets](microlabs/10-governance-stacksets) | StackSets, Organizations, EventBridge central | Multi-cuenta | ~USD 0 |
| 11 | [security-governance](microlabs/11-security-guardrails-rbac) | CloudTrail, Config, GuardDuty, Security Hub, RBAC, SCP | Gobernanza | ~USD 5-20/mes |

⚠️ Destruye los labs 06 y 08 al terminar cada sesión.

## Estructura

```
lab10_terraform_aws/
├── .gitlab-ci.yml            # plantillas del pipeline (validate → security → plan → apply → destroy)
├── DESPLIEGUE.md           # guía desde cero (herramientas, credenciales, orden)
├── sdk-examples/           # scripts cortos del SDK de IA
├── modules/                  # módulos compartidos y reutilizables
│   ├── kms-key/              # CMK con rotación
│   ├── s3-secure-bucket/     # BPA, versionado, SSE, TLS-only, lifecycle
│   ├── lambda-function/      # rol mínimo, logs JSON, X-Ray, arm64
│   ├── dynamodb-table/       # on-demand, PITR, TTL, GSI
│   ├── vpc/                  # 3 capas multi-AZ, NAT opcional, endpoints, flow logs
│   └── sns-alerts/           # tópico cifrado para alarmas
├── microlabs/NN-nombre/
│   ├── versions.tf           # providers + backend S3 parcial
│   ├── variables.tf · main.tf · outputs.tf
│   ├── terraform.tfvars.example
│   ├── ci.yml                # jobs de GitLab del lab
│   ├── README.md             # instrucciones, parámetros, WAF, storage mínimo
│   └── src/ templates/ policies/ ...
└── docs/                     # PDF de arquitecturas y su generador
```

## Orden recomendado

1. **00-platform-bootstrap-s3-oidc** (local, una vez): estado remoto + roles OIDC.
2. **11-security-guardrails-rbac**: auditoría activa antes de crear workloads.
3. Serverless: **01 → 02 → 03 → 04 → 05**.
4. **06** (3 niveles), luego **07** (SRE sobre 01/06).
5. Avanzados: **08** (Neptune), **09** (MGN), **10** (StackSets, requiere Organizations).

## Configuración de GitLab

### 1. CI/CD configuration file

Si el repositorio raíz es `Claude-Dev`: **Settings → CI/CD → General pipelines → CI/CD configuration file** = `lab10_terraform_aws/.gitlab-ci.yml`.

### 2. Variables (Settings → CI/CD → Variables)

| Variable | Tipo | Protegida | Enmascarada | Origen |
|---|---|---|---|---|
| `TF_STATE_BUCKET` | Variable | No | No | output de 00-platform-bootstrap-s3-oidc |
| `AWS_PLAN_ROLE_ARN` | Variable | No | Sí | output de 00-platform-bootstrap-s3-oidc |
| `AWS_APPLY_ROLE_ARN` | Variable | **Sí** | Sí | output de 00-platform-bootstrap-s3-oidc |
| `AWS_REGION` | Variable | No | No | `us-east-1` |
| `TF_ENV` | Variable | No | No | `dev` (usa environment scopes para `prod`) |
| `LAB01_TFVARS` … `LAB11_TFVARS` | **File** | Sí | No | contenido de `terraform.tfvars` de cada lab |
| `DESTROY_LAB` | Variable | No | No | se define al correr el pipeline manual, p. ej. `06-web3tier-alb-asg-rds` |

### 3. Protecciones

- **Protected branches**: `main` → *Allowed to merge*: Maintainers; *Allowed to push*: No one.
- **Merge request approvals**: 1 aprobación mínima; CODEOWNERS para `modules/` y `11-security-guardrails-rbac/`.
- **Protected environments**: `dev/*` y `prod/*` → solo Maintainers pueden ejecutar apply y destroy.
- **Pipeline must succeed** antes de hacer merge.

### 4. Flujo de trabajo

```
feature branch → MR → validate + tflint + checkov + plan (rol plan, solo lectura)
              → revisión del plan.txt (artifact) → merge a main
              → plan → apply MANUAL (rol apply, rama protegida) → outputs.json
destroy: Run pipeline en main con DESTROY_LAB=<lab> → job destroy manual
```

## Ejecución local (sin GitLab)

`scripts/lab.sh` encapsula init (con el backend correcto), plan, apply, test y destroy. Funciona en Linux, macOS y **Git Bash en Windows**.

```bash
cd lab10_terraform_aws
export AWS_PROFILE=<tu-perfil> AWS_REGION=us-east-1
# 1. Bootstrap (estado local, una sola vez)
cp microlabs/00-platform-bootstrap-s3-oidc/terraform.tfvars.example microlabs/00-platform-bootstrap-s3-oidc/terraform.tfvars
bash scripts/lab.sh init 00-platform-bootstrap-s3-oidc && bash scripts/lab.sh apply 00-platform-bootstrap-s3-oidc
export TF_STATE_BUCKET=$(terraform -chdir=microlabs/00-platform-bootstrap-s3-oidc output -raw tf_state_bucket)

# 2. Cualquier micro lab
cp microlabs/01-serverless-apigw-lambda-dynamodb/terraform.tfvars.example microlabs/01-serverless-apigw-lambda-dynamodb/terraform.tfvars
bash scripts/lab.sh init    01-serverless-apigw-lambda-dynamodb
bash scripts/lab.sh apply   01-serverless-apigw-lambda-dynamodb
bash scripts/lab.sh test    01-serverless-apigw-lambda-dynamodb     # smoke test de punta a punta
bash scripts/lab.sh destroy 01-serverless-apigw-lambda-dynamodb

# Utilidades
bash scripts/lab.sh validate-all                  # fmt/validate de los 12 labs sin credenciales
make apply LAB=06-web3tier-alb-asg-rds                  # equivalente con make
```

## Pruebas automatizadas (smoke tests)

Cada lab tiene `scripts/smoke-test.sh`, que **verifica el comportamiento real** de lo desplegado (no solo que exista). Las funciones comunes (lectura de outputs, `expect`, `retry`, usuarios temporales de Cognito) están en `scripts/lib.sh`. En CI corren en la etapa `smoke` después del apply, leyendo `outputs.json`.

| Lab | Qué demuestra la prueba |
|---|---|
| 00 | Bucket de estado seguro; OIDC con `sub` por rama; boundary niega `iam:CreateUser` |
| 01 | 200 / 401 / 403 / 400 / 201 / 204 / 404, throttling, access logs, X-Ray |
| 02 | Aislamiento entre dos usuarios, límite de profundidad, 401 |
| 03 | Ruteo por contenido, input transformer, auditoría y fallas en la DLQ |
| 04 | Respuesta del modelo, memoria en DynamoDB, guardrails (tema y prompt injection) |
| 05 | Step Functions SUCCEEDED con entidades + resumen; ruta de error FAILED |
| 06 | 2 AZ sanas, `/db` sobre TLS con Secrets Manager, RDS privado, WAF SQLi (`CHAOS=1` termina una instancia) |
| 07 | Canary PASSED, alarmas compuestas; `GENERATE_ERRORS=1` dispara el fast burn |
| 08 | Bulk load, 8 nodos y 9 aristas, consultas de recomendación y fraude |
| 09 | Landing zone segura; estado de replicación de los source servers |
| 10 | StackSet ACTIVE, instancias SUCCEEDED, drift IN_SYNC |
| 11 | Detectivos activos, preventivos, simulación RBAC, hallazgo de muestra |

> El repositorio vive en **GitHub**; el pipeline de este lab está escrito para **GitLab CI** (como pide el ejercicio). En GitHub, `.github/workflows/lab10-lab11-terraform.yml` ejecuta `fmt` y `validate` de ambos labs en cada PR.

## Requisitos

- Terraform ≥ 1.10 (bloqueo nativo de S3), AWS provider ~> 6.0
- AWS CLI v2 y jq (labs 09 y 10)
- Bedrock con acceso al modelo habilitado (labs 04 y 05)

## Estado de validación

Los 12 micro labs pasan `terraform fmt` y `terraform validate` (Terraform 1.13, AWS provider 6.x). **No se han desplegado** en una cuenta real, así que ejecuta `terraform plan` en tu cuenta antes de aplicar. Algunos valores dependen de la cuenta y la región (IDs de modelos de Bedrock, versión de Neptune, runtime de Synthetics, OUs) y están marcados en cada README.
