# Lab 11: Micro labs de Google Cloud con Terraform (SRE, serverless, IA y gobernanza)

Versión **GCP** del [lab10-terraform-aws](../lab10-terraform-aws): 17 micro labs (12 equivalentes a AWS + 5 de IA generativa) independientes y modulares para aprender a desplegar servicios de Google Cloud con Terraform, alineados con el **Google Cloud Architecture Framework** (equivalente al Well-Architected Framework). Se despliegan por GitOps desde **GitLab CI** con **Workload Identity Federation** (sin llaves JSON) y cada uno trae un **smoke test** que verifica el comportamiento real.

> 📄 Los diagramas, las tablas de implementación y la guía de RBAC y seguridad DevOps para GCP están en [docs/lab11-arquitecturas-gcp.pdf](docs/lab11-arquitecturas-gcp.pdf).

## Empieza aquí

| Si quieres... | Ve a |
|---|---|
| Instalar todo y desplegar desde cero | [DESPLIEGUE.md](DESPLIEGUE.md) |
| Practicar el SDK de IA (google-genai + Vertex AI) en scripts cortos | [sdk-examples/](sdk-examples/) |
| Ver la arquitectura de cada micro lab | [docs/lab11-arquitecturas-gcp.pdf](docs/lab11-arquitecturas-gcp.pdf) |
| Comparar con AWS | [docs/GUIA-AWS-GCP.md](docs/GUIA-AWS-GCP.md) |
| **Prepararte como Senior AI Engineer en Google** | [docs/SENIOR-GENAI-GCP.md](docs/SENIOR-GENAI-GCP.md) + micro labs GenAI 12-16 + sdk-examples 01-19 |

Cada carpeta de micro lab se llama `NN-categoria-servicios` (por ejemplo `03-genai-chatbot-vertex-gemini`) y su README empieza con **"Despliegue paso a paso"**.

## Índice

| # | Micro lab | Servicios | Equivalente en lab10-terraform-aws (AWS) | Costo si queda encendido |
|---|---|---|---|---|
| 00 | [bootstrap](microlabs/00-platform-bootstrap-gcs-wif) | GCS state, WIF, SAs, Artifact Registry, Budget | 00 (S3 + OIDC) | ~USD 0 |
| 01 | [api-gateway-functions](microlabs/01-serverless-apigw-functions-firestore) | API Gateway, Cloud Run functions, Firestore, API keys | 01 (API GW + Lambda) | Free tier |
| 02 | [pubsub-event-driven](microlabs/02-events-pubsub-scheduler) | Pub/Sub (schema, push OIDC, DLQ, filtros), BigQuery sub, Scheduler | 03 (EventBridge) | Free tier |
| 03 | [vertex-ai-chatbot](microlabs/03-genai-chatbot-vertex-gemini) | Vertex AI Gemini, Cloud Run functions, Firestore TTL | 04 (Bedrock) | Por token |
| 04 | [document-ai-workflows](microlabs/04-genai-docs-workflows) | Eventarc, Workflows, Vision, Natural Language, Gemini, BigQuery | 05 (Step Functions) | Por uso |
| 05 | [three-tier-web](microlabs/05-web3tier-lb-mig-cloudsql) | LB global, Cloud Armor, MIG regional, Cloud SQL HA, Secret Manager | 06 (ALB + RDS) | ~USD 120/mes ⚠️ |
| 06 | [gke-autopilot](microlabs/06-k8s-gke-autopilot) | GKE Autopilot, Workload Identity, HPA/PDB/NetworkPolicy | — (nuevo) | ~USD 95/mes ⚠️ |
| 07 | [sre-observability](microlabs/07-sre-slo-monitoring) | Cloud Monitoring SLOs, burn rate, uptime checks, dashboard | 07 (CloudWatch SLO) | Gratis |
| 08 | [bigquery-analytics](microlabs/08-data-bigquery-analytics) | BigQuery (capas, partición, vista autorizada), scheduled query | — (nuevo) | Free tier |
| 09 | [dms-migration](microlabs/09-migration-dms) | Database Migration Service, Cloud SQL, origen simulado | 09 (MGN) | ~USD 2/día ⚠️ |
| 10 | [org-governance](microlabs/10-governance-org-policies) | Carpetas, Org Policies, tags, firewall jerárquico, fábrica de proyectos | 10 (StackSets + SCP) | USD 0 |
| 11 | [security-governance](microlabs/11-security-iam-deny-rbac) | Audit logs, sinks, IAM Deny, RBAC, break-glass, SCC/VPC-SC | 11 (CloudTrail + GuardDuty) | Bajo |
| 12 | [genai-rag-bigquery-vector](microlabs/12-genai-rag-bigquery-vector) | BigQuery ML embeddings, VECTOR_SEARCH, Gemini con citas | 04 + RAG | Por uso |
| 13 | [genai-vertex-ai-search-grounding](microlabs/13-genai-vertex-ai-search-grounding) | Vertex AI Search, layout parser, grounding de Gemini | — (nuevo) | Por consulta |
| 14 | [genai-agent-adk](microlabs/14-genai-agent-adk) | Google ADK, herramientas sobre Firestore, sesiones | — (nuevo) | Por token |
| 15 | [genai-model-armor-safety](microlabs/15-genai-model-armor-safety) | Model Armor (injection, jailbreak, RAI, SDP, URLs) | Bedrock Guardrails (04) | Bajo |
| 16 | [genai-tuning-batch-eval](microlabs/16-genai-tuning-batch-eval) | SFT/LoRA de Gemini, batch prediction, evaluación | — (nuevo) | Por tokens |

## Estructura

```
03-cloud-e-infraestructura/lab11-terraform-gcp/
├── .gitlab-ci.yml          # plantillas: validate → security → plan → apply → smoke → destroy (WIF)
├── Makefile, scripts/      # lab.sh (init/plan/apply/test/destroy), lib.sh (helpers de smoke tests)
├── DESPLIEGUE.md           # guía desde cero (herramientas, credenciales, orden)
├── sdk-examples/           # scripts cortos del SDK de IA
├── modules/                # módulos compartidos de GCP
│   ├── project-services/   # habilita APIs + espera de propagación
│   ├── gcs-secure-bucket/  # UBLA, PAP enforced, versionado, CMEK, soft delete, lifecycle, retención
│   ├── service-account/    # SA dedicada + roles explícitos (nunca llaves)
│   ├── cloud-function/     # Cloud Run functions gen2 desde código fuente (sin Docker), invoker explícito
│   ├── vpc/                # subnets con PGA y flow logs, Cloud NAT, deny-all, IAP, PSA
│   └── kms-key/            # keyring + llave con rotación (sufijo aleatorio: los keyrings no se borran)
├── microlabs/NN-nombre/    # versions.tf · common_variables.tf · main.tf · variables.tf · outputs.tf
│                           # terraform.tfvars.example · ci.yml · README.md · scripts/smoke-test.sh · src/
└── docs/                   # PDF de arquitecturas y su generador
```

## Requisitos

- Terraform ≥ 1.10, providers `google` / `google-beta` ~> 7.0
- Google Cloud SDK (`gcloud`, `bq`, `kubectl` para el lab 06), `jq`, `curl`
- Un proyecto con facturación; para el lab 10, una **organización** y permisos de carpeta y políticas

## Orden recomendado

`00 → 11 → 01 → 02 → 03 → 04 → 07 (sobre 01) → 08 → 05 → 06 → 09 → 10`

**Ruta GenAI (Senior AI Engineer):** `00 → 03 → 12 → 13 → 14 → 15 → 16`, apoyándote en [docs/SENIOR-GENAI-GCP.md](docs/SENIOR-GENAI-GCP.md).

## Ejecución local

```bash
cd 03-cloud-e-infraestructura/lab11-terraform-gcp
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>

cp microlabs/00-platform-bootstrap-gcs-wif/terraform.tfvars.example microlabs/00-platform-bootstrap-gcs-wif/terraform.tfvars
bash scripts/lab.sh init 00-platform-bootstrap-gcs-wif && bash scripts/lab.sh apply 00-platform-bootstrap-gcs-wif
export TF_STATE_BUCKET=$(terraform -chdir=microlabs/00-platform-bootstrap-gcs-wif output -raw tf_state_bucket)

cp microlabs/01-serverless-apigw-functions-firestore/terraform.tfvars.example microlabs/01-serverless-apigw-functions-firestore/terraform.tfvars
bash scripts/lab.sh init  01-serverless-apigw-functions-firestore
bash scripts/lab.sh apply 01-serverless-apigw-functions-firestore
bash scripts/lab.sh test  01-serverless-apigw-functions-firestore
bash scripts/lab.sh destroy 01-serverless-apigw-functions-firestore

bash scripts/lab.sh validate-all      # fmt/validate de los 12 labs sin credenciales
```

## Configuración de GitLab

**CI/CD configuration file:** `03-cloud-e-infraestructura/lab11-terraform-gcp/.gitlab-ci.yml` (o inclúyelo desde un `.gitlab-ci.yml` raíz junto con lab10-terraform-aws).

| Variable | Tipo | Protegida | Origen |
|---|---|---|---|
| `GCP_PROJECT_ID` | Variable | No | tu proyecto |
| `TF_STATE_BUCKET` | Variable | No | output `tf_state_bucket` (lab 00) |
| `GCP_WIF_PROVIDER` | Variable | No | output `wif_provider` |
| `GCP_PLAN_SA` | Variable | No | output `plan_service_account` |
| `GCP_APPLY_SA` | Variable | **Sí** | output `apply_service_account` |
| `GCP01_TFVARS` … `GCP11_TFVARS` | **File** | Sí | `terraform.tfvars` de cada lab |
| `DESTROY_LAB` | Variable (al ejecutar) | No | nombre del lab a destruir |

**Cómo funciona la autenticación:** el job recibe un `id_token` de GitLab (`aud = https://gitlab.com`), escribe un archivo `external_account` y Terraform/gcloud lo intercambian en STS por un token de la SA. La SA de apply **solo** acepta tokens cuyo `deploy_ref` sea `<project_id>:branch:main`.

Protecciones: rama `main` protegida, approvals + CODEOWNERS, *protected environments* `gcp-dev/*` y `gcp-prod/*`.

## Pruebas automatizadas

| Lab | Qué demuestra |
|---|---|
| 00 | Bucket seguro, WIF ACTIVE con condición, SA apply sin llaves y solo desde main |
| 01 | 401 / 400 / **403 backend privado** / CRUD / **429 por cuota** |
| 02 | Schema rechaza mensajes inválidos, filtro por atributos, DLQ tras 5 intentos, BigQuery, Scheduler |
| 03 | 403 sin token, respuesta de Gemini, memoria, guardrails (tema + injection) |
| 04 | Workflow SUCCEEDED con entidades + resumen en BigQuery; FAILED; prefijo ignorado |
| 05 | 2 zonas sanas, `/db` por TLS e IP privada, SQL HA + PITR, Cloud Armor SQLi/XSS; `CHAOS=1` |
| 06 | Nodos privados, WI, PSA rechaza pod privilegiado, LB 200, PDB/NetworkPolicy; `LOAD=1` |
| 07 | SLOs y alertas; `GENERATE_ERRORS=1` → burn rate > 14.4 |
| 08 | Ingesta streaming, `require_partition_filter`, DLQ, MERGE programado, vista sin PII |
| 09 | Origen con pglogical (500/5000 filas), verify; `RUN_MIGRATION=1` → fase CDC |
| 10 | Org policies efectivas, baseline por proyecto, llave de SA bloqueada |
| 11 | Auditoría y sinks, **deny policy** bloquea llaves, evento en el log bucket, RBAC |
| 12 | Ingesta, respuesta con cita correcta, búsqueda semántica, "no tengo esa información" fuera de dominio |
| 13 | Indexación, grounding con fuentes (modo gemini) y resumen con citas (modo search) |
| 14 | El agente elige la herramienta correcta, usa memoria, no inventa pedidos y pide datos faltantes |
| 15 | Model Armor bloquea injection, datos sensibles y URLs maliciosas; deja auditoría |
| 16 | Dataset SFT, batch prediction terminada y exactitud del modelo base (`RUN_TUNING=1` para fine-tuning) |

> El repositorio vive en **GitHub**; `.github/workflows/lab10-lab11-terraform.yml` ejecuta `fmt` y `validate` de lab10-terraform-aws y lab11-terraform-gcp en cada PR. Los pipelines de este lab están escritos para **GitLab CI**.

## Estado de validación

Los 17 micro labs pasan `terraform fmt` y `terraform validate` (Terraform 1.13, google 7.x). **No se han desplegado** en un proyecto real: ejecuta `terraform plan` primero. Algunos valores dependen del proyecto y de la región (modelo de Gemini, IDs de organización y facturación) y están marcados en cada README.
