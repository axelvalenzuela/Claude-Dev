# Micro lab 00 — Bootstrap (estado remoto + GitLab OIDC + guardrails de costo)

> **Objetivo:** preparar la cuenta AWS para que el resto de los micro labs se desplieguen desde GitLab CI **sin llaves de acceso estáticas**, con estado remoto cifrado y alertas de presupuesto.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~2 min · **Costo si queda encendido:** ~USD 1/mes

**Prerrequisitos**

- Credenciales de administrador (`aws sso login`)

**1. Prepara las variables**

```bash
cd lab10_terraform_aws
cp microlabs/00-platform-bootstrap-s3-oidc/terraform.tfvars.example microlabs/00-platform-bootstrap-s3-oidc/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `owner` | tu correo |
| `gitlab_project_path` | `grupo/proyecto` exacto en GitLab |
| `alert_emails` | correo para el presupuesto |

**2. Despliega**

```bash
bash scripts/lab.sh init  00-platform-bootstrap-s3-oidc
bash scripts/lab.sh plan  00-platform-bootstrap-s3-oidc   # revisa qué se crea
bash scripts/lab.sh apply 00-platform-bootstrap-s3-oidc
```

**3. Después del apply**

- `export TF_STATE_BUCKET=$(terraform -chdir=microlabs/00-platform-bootstrap-s3-oidc output -raw tf_state_bucket)`
- Confirma el correo de AWS Budgets
- Copia los outputs a las variables de GitLab (si usarás CI)

**4. Verifica**

```bash
bash scripts/lab.sh test 00-platform-bootstrap-s3-oidc   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 00-platform-bootstrap-s3-oidc
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| main.tf → `data.aws_iam_policy_document.plan_trust/apply_trust` | Condición `sub` (`project_path:...:ref:main`) | Si usas otra rama protegida o tags de release |
| main.tf → `data.aws_iam_policy_document.boundary` | Regiones permitidas, acciones prohibidas | Para endurecer o relajar lo que el pipeline puede hacer |
| main.tf → `aws_iam_role_policy_attachment.apply` | Cambiar `AdministratorAccess` por políticas mínimas | En producción |
| variables.tf → `monthly_budget_usd` | Monto y umbrales del presupuesto | Según tu tarjeta / cuenta |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
GitLab CI job ──(id_token JWT, aud=https://gitlab.com)──► IAM OIDC Provider
        │                                                    │
        │  AssumeRoleWithWebIdentity                         ▼
        ├──► rol lab10-dev-gitlab-plan   (ReadOnly + estado)   ← cualquier rama/MR
        └──► rol lab10-dev-gitlab-apply  (Admin ∩ Boundary)    ← solo rama main
                                   │
                                   ▼
             S3 lab10-dev-tfstate-<account>  (SSE-KMS, versionado, solo TLS, *.tflock)
```

## Recursos

| Recurso | Propósito |
|---|---|
| `module.state_key` (KMS) | Cifra el estado de Terraform |
| `module.state_bucket` (S3) | Estado remoto; bloqueo nativo `use_lockfile` (Terraform ≥ 1.10, ya no requiere DynamoDB) |
| `aws_iam_openid_connect_provider.gitlab` | Federación OIDC con GitLab |
| `aws_iam_role.plan` / `.apply` | Separación de funciones: plan en MRs, apply solo en `main` |
| `aws_iam_policy.boundary` | Tope de permisos: regiones permitidas, no tocar CloudTrail/GuardDuty/Config, no crear usuarios IAM |
| `aws_budgets_budget.monthly` | Alertas al 50 % / 80 % (real) y 100 % (pronóstico) |

## Pasos

1. Autentícate localmente con un usuario/rol administrador (`aws sso login` o `aws configure`).
2. `cp terraform.tfvars.example terraform.tfvars` y edita `owner`, `gitlab_project_path`, `alert_emails`.
3. Despliega con estado local:
   ```bash
   terraform init
   terraform plan -out tfplan
   terraform apply tfplan
   terraform output
   ```
4. (Opcional) Migra el propio estado del bootstrap al bucket: descomenta `backend "s3" {}` en `versions.tf` y ejecuta
   ```bash
   terraform init -migrate-state \
     -backend-config="bucket=$(terraform output -raw tf_state_bucket)" \
     -backend-config="key=lab10_terraform_aws/00-platform-bootstrap-s3-oidc/terraform.tfstate" \
     -backend-config="region=us-east-1" -backend-config="use_lockfile=true" -backend-config="encrypt=true"
   ```
5. Copia los outputs a GitLab (ver tabla abajo) y confirma los correos de AWS Budgets.

## Parámetros a configurar en GitLab (Settings → CI/CD → Variables)

| Variable | Valor | Protegida | Enmascarada |
|---|---|---|---|
| `TF_STATE_BUCKET` | output `tf_state_bucket` | No | No |
| `AWS_PLAN_ROLE_ARN` | output `aws_plan_role_arn` | No | Sí |
| `AWS_APPLY_ROLE_ARN` | output `aws_apply_role_arn` | **Sí** | Sí |
| `AWS_REGION` | `us-east-1` | No | No |

Además: **Settings → Repository → Protected branches**: protege `main` (solo Maintainers hacen merge).

<!-- detalle-funcional -->
## Ejecución rápida

```bash
cd lab10_terraform_aws
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/00-platform-bootstrap-s3-oidc/terraform.tfvars.example microlabs/00-platform-bootstrap-s3-oidc/terraform.tfvars   # edita owner y demás
bash scripts/lab.sh init  00-platform-bootstrap-s3-oidc
bash scripts/lab.sh apply 00-platform-bootstrap-s3-oidc
bash scripts/lab.sh test  00-platform-bootstrap-s3-oidc      # smoke test automatizado (abajo)
bash scripts/lab.sh destroy 00-platform-bootstrap-s3-oidc
```

Con `make`: `make apply LAB=00-platform-bootstrap-s3-oidc` · `make test LAB=00-platform-bootstrap-s3-oidc`. Requisitos del smoke test: AWS CLI v2, `jq`, `curl` y credenciales con permisos de escritura sobre el lab.

## Prueba automatizada (`scripts/smoke-test.sh`)

Verifica: versionado y cifrado KMS del bucket de estado, Block Public Access, política TLS-only, acceso anónimo denegado, trust policies OIDC (plan = `ref:*`, apply = `ref:main`), permissions boundary del rol apply (simula `iam:CreateUser` → `explicitDeny`) y existencia del presupuesto.

### Resultado esperado (extracto)

```
== Bucket de estado: lab10-dev-tfstate-123456789012
  OK   Versionado (Enabled)
  OK   Cifrado (aws:kms)
  OK   Block Public Access (True)
  OK   Política exige TLS
  OK   Acceso anónimo denegado (HTTP 403)
== Roles de CI (OIDC)
  OK   Rol plan acepta cualquier rama
  OK   Rol apply solo acepta main
== Simulación del boundary (el rol apply NO puede crear usuarios IAM)
  OK   iam:CreateUser (explicitDeny)
SMOKE TEST OK  (11 verificaciones)
```

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `EntityAlreadyExists` en el OIDC provider | Ya existe un proveedor para gitlab.com en la cuenta (máximo uno por URL). Impórtalo: `terraform import aws_iam_openid_connect_provider.gitlab arn:aws:iam::<cuenta>:oidc-provider/gitlab.com`. |
| El job de GitLab falla con `Not authorized to perform sts:AssumeRoleWithWebIdentity` | `gitlab_project_path` no coincide exactamente con el proyecto (incluye subgrupos) o el `aud` del `id_tokens` es distinto de `gitlab_audience`. Revisa el claim `sub` con `echo $GITLAB_OIDC_TOKEN | cut -d. -f2 | base64 -d`. |
| `BucketAlreadyExists` | Los nombres de S3 son globales; el sufijo con el ID de cuenta normalmente lo evita. Cambia `project`. |
<!-- detalle-funcional -->

## Well-Architected

| Pilar | Cómo se aplica |
|---|---|
| Excelencia operativa | Todo como código; estado remoto versionado; pipeline GitOps |
| Seguridad | OIDC (sin secretos), mínimo privilegio, boundary, KMS, TLS obligatorio |
| Confiabilidad | Versionado del estado + retención de versiones previas 90 días |
| Eficiencia de rendimiento | N/A (plano de control) |
| Optimización de costos | AWS Budgets; S3 con lifecycle |
| Sostenibilidad | Sin infraestructura ociosa: solo recursos serverless/gestionados |

## Storage mínimo

| Elemento | Definición |
|---|---|
| S3 estado | < 1 MB por micro lab, Standard, versionado |
| KMS | 1 CMK (~USD 1/mes) |

## Limpieza

El bucket tiene `force_destroy = false` a propósito. Destruye primero todos los micro labs; luego vacía el bucket manualmente y ejecuta `terraform destroy`.
