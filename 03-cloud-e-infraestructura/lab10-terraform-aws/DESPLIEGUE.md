# Despliegue desde cero: lab10-terraform-aws (AWS)

Guía completa para pasar de una computadora sin nada instalado a tener los micro labs desplegados, probados y destruidos. Cada micro lab tiene además su propia sección **"Despliegue paso a paso"** en su README.

**Tiempo total de la preparación (pasos 1 a 4):** ~45 minutos, una sola vez.

---

## Paso 1. Cuenta de AWS segura

1. Crea una cuenta en <https://aws.amazon.com> (requiere tarjeta; los labs serverless entran en la capa gratuita).
2. Activa **MFA en el usuario root** (IAM → Security credentials) y no vuelvas a usar root para trabajar.
3. Activa **IAM Identity Center** (región `us-east-1`) y crea un usuario para ti con el permission set `AdministratorAccess`. Guarda la URL del portal de acceso (`https://d-xxxxxxxxxx.awsapps.com/start`).
4. En **Billing → Budgets** crea un presupuesto de USD 10 como red de seguridad (el lab 00 crea otro con Terraform).

> Para los labs 04 y 05: **Bedrock → Model access** → habilita el modelo que vayas a usar (por defecto `Amazon Nova Lite`) en `us-east-1`.

## Paso 2. Herramientas en tu computadora

### Windows (PowerShell)

```powershell
winget install --id Git.Git -e
winget install --id Hashicorp.Terraform -e
winget install --id Amazon.AWSCLI -e
winget install --id jqlang.jq -e
winget install --id Python.Python.3.13 -e
# Cierra y abre la terminal. Usa "Git Bash" para correr los scripts .sh de los labs.
```

### macOS

```bash
brew install git terraform awscli jq python@3.13
```

### Linux (Debian/Ubuntu)

```bash
sudo apt-get update && sudo apt-get install -y git jq python3 unzip curl
curl -fsSL https://releases.hashicorp.com/terraform/1.13.0/terraform_1.13.0_linux_amd64.zip -o tf.zip && sudo unzip -o tf.zip -d /usr/local/bin
curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o aws.zip && unzip -q aws.zip && sudo ./aws/install
```

### Verifica

```bash
terraform version     # >= 1.10
aws --version         # aws-cli/2.x
jq --version
```

## Paso 3. Credenciales (sin llaves de acceso)

```bash
aws configure sso
#   SSO start URL : https://d-xxxxxxxxxx.awsapps.com/start
#   SSO region    : us-east-1
#   Cuenta / rol  : tu cuenta / AdministratorAccess
#   Profile name  : lab10
export AWS_PROFILE=lab10 AWS_REGION=us-east-1      # en cada terminal nueva
aws sso login                                       # cuando expire la sesión
aws sts get-caller-identity                         # debe mostrar tu cuenta
```

## Paso 4. Clonar el repositorio y desplegar el bootstrap (lab 00)

```bash
git clone https://github.com/<tu-usuario>/Claude-Dev.git
cd Claude-Dev/03-cloud-e-infraestructura/lab10-terraform-aws

cp microlabs/00-platform-bootstrap-s3-oidc/terraform.tfvars.example microlabs/00-platform-bootstrap-s3-oidc/terraform.tfvars
#   edita: owner, gitlab_project_path, alert_emails
bash scripts/lab.sh init  00-platform-bootstrap-s3-oidc
bash scripts/lab.sh apply 00-platform-bootstrap-s3-oidc
bash scripts/lab.sh test  00-platform-bootstrap-s3-oidc

export TF_STATE_BUCKET=$(terraform -chdir=microlabs/00-platform-bootstrap-s3-oidc output -raw tf_state_bucket)
echo "export TF_STATE_BUCKET=$TF_STATE_BUCKET" >> ~/.bashrc   # para no repetirlo
```

Confirma el correo de suscripción de AWS Budgets.

## Paso 5. Ciclo de cada micro lab

```bash
LAB=01-serverless-apigw-lambda-dynamodb
cp microlabs/$LAB/terraform.tfvars.example microlabs/$LAB/terraform.tfvars   # edita owner y lo que pida su README
bash scripts/lab.sh init    $LAB      # backend S3 con key 03-cloud-e-infraestructura/lab10-terraform-aws/$LAB/dev.tfstate
bash scripts/lab.sh plan    $LAB      # revisa qué se va a crear
bash scripts/lab.sh apply   $LAB
bash scripts/lab.sh test    $LAB      # smoke test: debe terminar en "SMOKE TEST OK"
bash scripts/lab.sh destroy $LAB      # al terminar la sesión
```

Orden recomendado y prerrequisitos:

| Orden | Micro lab | Prerrequisito extra | Tiempo de apply |
|---|---|---|---|
| 1 | `11-security-guardrails-rbac` | — | ~3 min |
| 2 | `01-serverless-apigw-lambda-dynamodb` | — | ~2 min |
| 3 | `02-serverless-appsync-graphql` | — | ~2 min |
| 4 | `03-events-eventbridge-sqs` | — | ~2 min |
| 5 | `04-genai-chatbot-bedrock` | Model access en Bedrock | ~3 min |
| 6 | `05-genai-docs-stepfunctions` | Model access en Bedrock | ~3 min |
| 7 | `06-web3tier-alb-asg-rds` | — (cuesta ~USD 3/día) | ~15 min |
| 8 | `07-sre-slo-cloudwatch-fis` | lab 01 desplegado | ~3 min |
| 9 | `08-data-neptune-graph` | — (cuesta ~USD 4/día) | ~15 min |
| 10 | `09-migration-mgn` | IP del servidor origen | ~3 min + agente |
| 11 | `10-governance-stacksets` | AWS Organizations (cuenta management) | ~5 min |

## Paso 6 (opcional). Pipeline en GitLab

1. Importa el repositorio en GitLab (*New project → Import project → Repository by URL*).
2. **Settings → CI/CD → General pipelines → CI/CD configuration file:** `03-cloud-e-infraestructura/lab10-terraform-aws/.gitlab-ci.yml`.
3. **Settings → CI/CD → Variables:** `TF_STATE_BUCKET`, `AWS_PLAN_ROLE_ARN`, `AWS_APPLY_ROLE_ARN` (protegida), `AWS_REGION` y un `LABNN_TFVARS` (tipo **File**) por lab.
4. **Settings → Repository → Protected branches:** `main` (merge solo Maintainers).
5. Crea una rama, cambia algo en un lab y abre un MR: verás validate → checkov → plan. Al hacer merge: apply (manual) → smoke.

## Paso 7. Limpieza total

```bash
for LAB in $(ls microlabs | grep -v 00-platform | sort -r); do bash scripts/lab.sh destroy $LAB; done
# El bucket de estado tiene force_destroy = false: vacíalo y destruye el bootstrap al final
aws s3 rm s3://$TF_STATE_BUCKET --recursive
bash scripts/lab.sh destroy 00-platform-bootstrap-s3-oidc
```

## Problemas comunes al empezar

| Síntoma | Solución |
|---|---|
| `bash: scripts/lab.sh: No such file` en Windows | Usa **Git Bash**, no PowerShell, y ejecuta desde `03-cloud-e-infraestructura/lab10-terraform-aws/` |
| `ExpiredToken` / `The SSO session has expired` | `aws sso login` |
| `Error: Backend initialization required` | Corre `bash scripts/lab.sh init <lab>` (cada lab tiene su propio estado) |
| `TF_STATE_BUCKET: parameter null or not set` | Exporta la variable del paso 4 |
| Error de `\r` en scripts (`$'\r': command not found`) | Clonaste con CRLF: `git config core.autocrlf input` y vuelve a clonar (el `.gitattributes` fuerza LF en archivos nuevos) |
