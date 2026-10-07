# Despliegue desde cero: lab11_terraform_gcp (Google Cloud)

Guía completa para pasar de una computadora sin nada instalado a tener los micro labs desplegados, probados y destruidos. Cada micro lab tiene además su propia sección **"Despliegue paso a paso"** en su README.

**Tiempo total de la preparación (pasos 1 a 4):** ~40 minutos, una sola vez.

---

## Paso 1. Proyecto de Google Cloud

1. Entra a <https://console.cloud.google.com> con tu cuenta (los nuevos usuarios reciben crédito de prueba).
2. **Billing → Create billing account** (tarjeta) y anota su ID `XXXXXX-XXXXXX-XXXXXX`.
3. Crea un proyecto dedicado, por ejemplo `labs-<tus-iniciales>-2026`, y vincúlalo a la facturación.
4. **Billing → Budgets & alerts:** crea un presupuesto de USD 10 como red de seguridad (el lab 00 crea otro con Terraform).
5. Solo para `10-governance-org-policies`: necesitas una **organización** (Cloud Identity Free o Google Workspace) y crear el proyecto dentro de ella.

## Paso 2. Herramientas en tu computadora

### Windows (PowerShell)

```powershell
winget install --id Git.Git -e
winget install --id Hashicorp.Terraform -e
winget install --id Google.CloudSDK -e
winget install --id jqlang.jq -e
winget install --id Python.Python.3.13 -e
# Cierra y abre la terminal. Usa "Git Bash" para correr los scripts .sh de los labs.
gcloud components install kubectl gke-gcloud-auth-plugin   # solo para el lab 06
```

### macOS

```bash
brew install git terraform jq python@3.13
brew install --cask google-cloud-sdk
gcloud components install kubectl gke-gcloud-auth-plugin
```

### Linux (Debian/Ubuntu)

```bash
sudo apt-get update && sudo apt-get install -y git jq python3 unzip curl apt-transport-https ca-certificates gnupg
curl -fsSL https://releases.hashicorp.com/terraform/1.13.0/terraform_1.13.0_linux_amd64.zip -o tf.zip && sudo unzip -o tf.zip -d /usr/local/bin
curl -sSL https://sdk.cloud.google.com | bash && exec -l $SHELL
gcloud components install kubectl gke-gcloud-auth-plugin
```

### Verifica

```bash
terraform version     # >= 1.10
gcloud version
bq version
jq --version
```

## Paso 3. Credenciales (sin llaves JSON)

```bash
gcloud auth login                         # identidad para gcloud
gcloud auth application-default login     # identidad para Terraform y los SDK (ADC)
gcloud config set project <PROJECT_ID>
gcloud auth application-default set-quota-project <PROJECT_ID>
export GOOGLE_CLOUD_PROJECT=<PROJECT_ID>  # en cada terminal nueva
```

> Nunca descargues llaves JSON de service accounts: el lab 10 incluso las prohíbe con una Org Policy.

## Paso 4. Clonar el repositorio y desplegar el bootstrap (lab 00)

```bash
git clone https://github.com/<tu-usuario>/Claude-Dev.git
cd Claude-Dev/lab11_terraform_gcp

cp microlabs/00-platform-bootstrap-gcs-wif/terraform.tfvars.example microlabs/00-platform-bootstrap-gcs-wif/terraform.tfvars
#   edita: project_id, owner, gitlab_project_path, gitlab_project_id, billing_account, alert_email
bash scripts/lab.sh init  00-platform-bootstrap-gcs-wif
bash scripts/lab.sh apply 00-platform-bootstrap-gcs-wif
bash scripts/lab.sh test  00-platform-bootstrap-gcs-wif

export TF_STATE_BUCKET=$(terraform -chdir=microlabs/00-platform-bootstrap-gcs-wif output -raw tf_state_bucket)
terraform -chdir=microlabs/00-platform-bootstrap-gcs-wif output -raw build_service_account   # cópialo a build_service_account de los labs con funciones
echo "export TF_STATE_BUCKET=$TF_STATE_BUCKET" >> ~/.bashrc
```

## Paso 5. Ciclo de cada micro lab

```bash
LAB=01-serverless-apigw-functions-firestore
cp microlabs/$LAB/terraform.tfvars.example microlabs/$LAB/terraform.tfvars   # edita project_id, owner y lo que pida su README
bash scripts/lab.sh init    $LAB      # backend GCS con prefix lab11_terraform_gcp/$LAB/dev
bash scripts/lab.sh plan    $LAB
bash scripts/lab.sh apply   $LAB
bash scripts/lab.sh test    $LAB      # debe terminar en "SMOKE TEST OK"
bash scripts/lab.sh destroy $LAB
```

Orden recomendado y prerrequisitos:

| Orden | Micro lab | Prerrequisito extra | Tiempo de apply |
|---|---|---|---|
| 1 | `11-security-iam-deny-rbac` | — | ~3 min |
| 2 | `01-serverless-apigw-functions-firestore` | `build_service_account` del lab 00 | ~6 min |
| 3 | `02-events-pubsub-scheduler` | `build_service_account` | ~6 min |
| 4 | `03-genai-chatbot-vertex-gemini` | `invoker_members` con tu correo | ~5 min |
| 5 | `04-genai-docs-workflows` | — | ~4 min |
| 6 | `07-sre-slo-monitoring` | lab 01 desplegado | ~2 min |
| 7 | `08-data-bigquery-analytics` | — | ~2 min |
| 8 | `05-web3tier-lb-mig-cloudsql` | — (cuesta ~USD 4/día) | ~20 min |
| 9 | `06-k8s-gke-autopilot` | tu IP en `authorized_networks` (cuesta ~USD 3/día) | ~12 min |
| 10 | `09-migration-dms` | — (cuesta ~USD 2/día) | ~15 min |
| 11 | `10-governance-org-policies` | organización + permisos de admin | ~5 min |
| 12 | `12-genai-rag-bigquery-vector` | `invoker_members`; luego `scripts/ingest.py` | ~6 min |
| 13 | `13-genai-vertex-ai-search-grounding` | `invoker_members`; luego `scripts/import-docs.sh --wait` | ~4 min + indexación |
| 14 | `14-genai-agent-adk` | `invoker_members` | ~6 min |
| 15 | `15-genai-model-armor-safety` | `invoker_members`, región con Model Armor | ~5 min |
| 16 | `16-genai-tuning-batch-eval` | `pip install -r scripts/requirements.txt` (el tuning tiene costo) | ~2 min |

## Paso 6 (opcional). Pipeline en GitLab

1. Importa el repositorio en GitLab.
2. **CI/CD configuration file:** `lab11_terraform_gcp/.gitlab-ci.yml`.
3. **Variables:** `GCP_PROJECT_ID`, `TF_STATE_BUCKET`, `GCP_WIF_PROVIDER`, `GCP_PLAN_SA`, `GCP_APPLY_SA` (protegida) y `GCPNN_TFVARS` (tipo **File**) por lab. Los valores salen de `terraform output` del lab 00.
4. Protege `main` y crea un MR de prueba: validate → checkov → plan; al hacer merge: apply (manual) → smoke.

## Paso 7. Limpieza total

```bash
for LAB in $(ls microlabs | grep -v 00-platform | sort -r); do bash scripts/lab.sh destroy $LAB; done
gcloud storage rm -r "gs://$TF_STATE_BUCKET/**"
bash scripts/lab.sh destroy 00-platform-bootstrap-gcs-wif
# Opcional: borrar el proyecto completo (se puede recuperar durante 30 días)
gcloud projects delete <PROJECT_ID>
```

## Problemas comunes al empezar

| Síntoma | Solución |
|---|---|
| `could not find default credentials` | `gcloud auth application-default login` |
| `API ... has not been used in project ... or it is disabled` | Espera 1-2 min: cada lab habilita sus APIs y Terraform reintenta; vuelve a aplicar si persiste |
| `Error 403: ... billing account` | El proyecto no tiene facturación vinculada (paso 1.3) |
| Build de funciones falla con permisos | Pasa `build_service_account` del lab 00 en el tfvars |
| `$'\r': command not found` | `git config core.autocrlf input` y vuelve a clonar |
