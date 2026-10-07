# Micro lab 00 (GCP): Bootstrap: estado remoto, Workload Identity Federation y guardrails de costo

> **Objetivo:** Preparar el proyecto para desplegar todos los labs desde GitLab **sin llaves JSON de service accounts**, con estado remoto versionado, separación plan/apply y presupuesto.

## Arquitectura

```
GitLab CI job ──id_token (aud = https://gitlab.com)──► STS (Workload Identity Federation)
        │                                   pool lab11-dev-gitlab · provider gitlab
        │                                   condición: assertion.project_path == '<grupo/proyecto>'
        ├─ impersona lab11-dev-tf-plan   (viewer + securityReviewer)     ← cualquier rama/MR
        └─ impersona lab11-dev-tf-apply  (roles de despliegue)           ← solo deploy_ref = <id>:branch:main
                          │
                          ▼
        gs://<project>-lab11-tfstate  (versionado, UBLA, PAP enforced, soft delete 30 d, lock nativo)
        lab11-dev-builder (Cloud Build para Cloud Run functions) · Artifact Registry lab11 · Budget
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `module.services` | APIs base (IAM, STS, Storage, Cloud Build, Artifact Registry, Budgets) |
| `module.state_bucket` | Estado de Terraform (GCS bloquea el estado de forma nativa) |
| `google_iam_workload_identity_pool(_provider)` | Federación OIDC con GitLab; mapeo de claims y condición por proyecto |
| `module.plan_sa` / `module.apply_sa` | Separación de funciones; bindings `workloadIdentityUser` por atributo |
| `module.builder_sa` | Identidad de Cloud Build para construir funciones (evita la SA de compute por defecto) |
| `google_artifact_registry_repository` | Imágenes con políticas de limpieza (keep 10, borrar untagged > 7 d) |
| `google_billing_budget` | 50 / 80 % real y 100 % pronosticado (si `billing_account` está definido) |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `project_id` | — | Proyecto con facturación |
| `gitlab_project_path` | — | `grupo/proyecto` exacto |
| `gitlab_project_id` | — | ID numérico del proyecto GitLab |
| `apply_roles` | lista | Ajusta a lo mínimo |
| `billing_account` | `null` | Para el presupuesto |
| `alert_email` | `null` | Canal de notificación |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd lab11
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/00-bootstrap/terraform.tfvars.example microlabs/00-bootstrap/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  00-bootstrap
bash scripts/lab.sh apply 00-bootstrap
bash scripts/lab.sh test  00-bootstrap
bash scripts/lab.sh destroy 00-bootstrap
```

Este lab se aplica con **estado local** (el bucket aún no existe). Después puedes migrarlo:
descomenta `backend "gcs" {}` en `versions.tf` y ejecuta
`terraform init -migrate-state -backend-config=bucket=$(terraform output -raw tf_state_bucket) -backend-config=prefix=lab11/00-bootstrap`.

## Prueba automatizada (`scripts/smoke-test.sh`)

Bucket con versionado, UBLA y public access prevention; acceso anónimo 401; provider WIF `ACTIVE` con condición por proyecto; el SA de apply **sin llaves JSON** y solo impersonable desde `branch:main`; el SA de plan con `roles/viewer`.

### Resultado esperado (extracto)

```
== Bucket de estado gs://mi-proyecto-lab11-tfstate
  OK   Versionado (true)
  OK   Public access prevention (enforced)
== Workload Identity Federation
  OK   Estado del provider (ACTIVE)
== Service accounts
  OK   Llaves JSON del SA apply (user-managed) (0)
  OK   SA apply solo impersonable desde la rama main
SMOKE TEST OK  (9 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `TF_STATE_BUCKET` | Variable | output `tf_state_bucket` |
| `GCP_WIF_PROVIDER` | Variable | output `wif_provider` |
| `GCP_PLAN_SA` | Variable | output `plan_service_account` |
| `GCP_APPLY_SA` | Variable **protegida** | output `apply_service_account` |
| `GCP_PROJECT_ID` | Variable | tu proyecto |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `Error 409: Requested entity already exists` en el pool | Los pools borrados quedan 30 días en *soft delete*. Restáuralo (`gcloud iam workload-identity-pools undelete`) o cambia `environment`. |
| El job falla con `Permission 'iam.serviceAccounts.getAccessToken' denied` | El `deploy_ref` no coincide: el pipeline no es de `main` o `gitlab_project_id` es incorrecto. |
| `The caller does not have permission` al crear el budget | Necesitas `roles/billing.costsManager` en la cuenta de facturación; o deja `billing_account = null`. |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | IaC + estado versionado; pipeline GitOps |
| Seguridad | WIF sin llaves; condición por proyecto; apply solo en main |
| Confiabilidad | Versionado + soft delete del estado |
| Rendimiento | N/A (plano de control) |
| Costos | Budget con pronóstico; limpieza de Artifact Registry |
| Sostenibilidad | Solo servicios administrados |

## Storage mínimo

| Recurso | Definición |
|---|---|
| GCS estado | < 1 MB por lab; STANDARD regional; versiones previas 90 días |

**Costo aproximado:** Prácticamente gratis (GCS + Artifact Registry por uso).
