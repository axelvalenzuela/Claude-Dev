# Pipelines de automatización (lab 6)

Automatizan todo el camino: validar → dimensionar → planificar → aprobar →
crear infraestructura → configurar el sistema. Solo hay que cargar secretos,
licencias y medios ([../ASSESSMENT.md](../ASSESSMENT.md), sección 1).

| Archivo | Plataforma |
|---|---|
| [../../.github/workflows/lab6-sap-pipeline.yml](../../.github/workflows/lab6-sap-pipeline.yml) | GitHub Actions (el remoto actual de este repo) |
| [gitlab-ci.yml](gitlab-ci.yml) | GitLab CI (equivalente) |

> Estado: `terraform validate`, `tools/sizing.js` y `tools/tf-to-inventory.js`
> se probaron localmente. Los workflows/pipelines y los roles de Ansible **no
> se ejecutaron** (no hay cuenta AWS, Ansible ni GitLab en esta máquina):
> revisarlos y probarlos primero en `dev`.

## Etapas

| Etapa | Cuándo corre | Qué hace |
|---|---|---|
| `validate` | Cada push / PR que toque `lab6/` | Sizing de prueba, `terraform fmt/validate`, sintaxis de Ansible. No necesita credenciales |
| `prepare` | Manual | Lee el entorno del assessment |
| `plan` | Manual (`plan` o `apply`) | Sizing → tfvars, `terraform plan`, guarda el plan como artefacto |
| `apply` | Manual (`apply`) | **Aprobación humana** (entorno protegido) y `terraform apply` del plan guardado |
| `configure` | Manual (`configure` o tras `apply`) | Genera el inventario desde los outputs de Terraform y corre Ansible por SSM |

Ansible (`ansible/playbooks/site.yml`): `os_prepare` (paquetes, chrony,
saptune/tuned) → `storage` (formatea y monta discos por ID de volumen) →
`hana_install` (hdblcm, base tenant, licencia) → `hana_replication` (HSR
primario/secundario si `ha_enabled`) → `s4_install` (SWPM + licencia ABAP,
solo si se pide).

## Configuración única

1. **Estado de Terraform:** crear un bucket S3 (versionado, cifrado) y una tabla DynamoDB con clave `LockID` (string).
2. **Rol IAM con OIDC** para el pipeline. Confianza de ejemplo (GitHub):
   ```json
   {
     "Effect": "Allow",
     "Principal": { "Federated": "arn:aws:iam::<CUENTA>:oidc-provider/token.actions.githubusercontent.com" },
     "Action": "sts:AssumeRoleWithWebIdentity",
     "Condition": {
       "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
       "StringLike":   { "token.actions.githubusercontent.com:sub": "repo:axelvalenzuela/Claude-Dev:*" }
     }
   }
   ```
   Permisos del rol: los que necesita lo que crea Terraform (EC2, VPC, EBS, KMS, IAM roles/perfiles, S3), acceso al estado, y para Ansible por SSM: `ssm:StartSession`, `ssm:SendCommand`, `ssm:GetCommandInvocation` y acceso al bucket de backup (transferencia de archivos). Acotarlos, no usar administrador.
3. **Medios de SAP** en el bucket `SAP_MEDIA_BUCKET` (estructura en ASSESSMENT.md).
4. **GitHub:** crear los entornos `sap-dev`, `sap-qas`, `sap-prd` y agregar *Required reviewers* (es lo que da la aprobación antes de `apply`/`configure`).
5. **Variables y secretos** (Settings → Secrets and variables → Actions):

| Tipo | Nombre | Contenido |
|---|---|---|
| Variable | `AWS_ROLE_ARN`, `AWS_REGION` | Rol OIDC y región |
| Variable | `TF_STATE_BUCKET`, `TF_STATE_LOCK_TABLE` | Estado remoto |
| Variable | `SAP_MEDIA_BUCKET` | Bucket de medios |
| Variable | `SWPM_PRODUCT_ID` | Solo si se instala S/4HANA |
| Secret | `HANA_SYSTEM_PASSWORD`, `HANA_SIDADM_PASSWORD`, `HANA_SAPADM_PASSWORD` | Contraseñas de HANA |
| Secret | `S4_MASTER_PASSWORD` | Contraseña maestra de S/4HANA |
| Secret | `HANA_LICENSE_TEXT`, `S4_LICENSE_TEXT` | Contenido de los archivos de licencia |

Idealmente los secretos van como **secretos del entorno** (`sap-<env>`), no del repositorio.

## Ejecución

GitHub → Actions → **lab6-sap-pipeline** → *Run workflow*:

1. `action = plan` con tu assessment (`lab6/assessment/mi-dev.json`): revisar el plan.
2. `action = apply`: tras la aprobación crea la infraestructura.
3. `action = configure` (o el mismo `apply`, que continúa solo): configura el sistema. Con `run_s4_install = true` instala S/4HANA.

En GitLab: copiar/incluir `gitlab-ci.yml`, definir las variables equivalentes y lanzar el pipeline desde *Run pipeline*; `apply` y `configure` son manuales.

## Seguridad del pipeline

- Sin llaves de AWS guardadas: credenciales temporales por OIDC.
- Acceso a las máquinas por SSM, sin SSH ni IP pública.
- Los pasos con contraseñas usan `no_log`. Aun así, `hdbsql -p` deja la contraseña en la lista de procesos durante segundos: para producción, migrar a `hdbuserstore`.
- El archivo de licencia y de parámetros de SWPM se escriben con permisos `0600` y se borran al terminar.
- `apply` usa el plan aprobado (`tfplan`), no recalcula.
