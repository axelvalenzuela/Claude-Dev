# Micro lab 11 (GCP): Seguridad y gobernanza del proyecto: auditoría, deny policies, RBAC y alertas

> **Objetivo:** Controles detectivos y preventivos de un proyecto: Data Access logs, archivo inmutable, alertas sobre eventos de alto riesgo, IAM Deny Policy, RBAC por función y break-glass temporal.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y micro lab 00).

**Tiempo de apply:** ~3 min · **Costo si queda encendido:** Bajo

**Prerrequisitos**

- Micro lab 00
- Aplícalo **antes** que los demás labs

**1. Prepara las variables**

```bash
cd 06-terraform-gcp
cp microlabs/11-security-iam-deny-rbac/terraform.tfvars.example microlabs/11-security-iam-deny-rbac/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `security_emails` | alertas |
| `rbac_members` | grupos por equipo |
| `deny_exception_principals` | tu identidad si activas `protect_audit_sinks` |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del micro lab 00>
bash scripts/lab.sh init  11-security-iam-deny-rbac
bash scripts/lab.sh plan  11-security-iam-deny-rbac   # revisa qué se crea
bash scripts/lab.sh apply 11-security-iam-deny-rbac
```

**3. Después del apply**

- Intenta crear una llave de SA: debe fallar por la deny policy

**4. Verifica**

```bash
bash scripts/lab.sh test 11-security-iam-deny-rbac   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 11-security-iam-deny-rbac
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| main.tf → `locals.rbac` | Roles por equipo | Según tu organización |
| main.tf → `google_project_iam_custom_role.deployer.permissions` | Permisos del rol custom | Mínimo privilegio |
| main.tf → `google_iam_deny_policy.guardrails` | Permisos denegados | Nuevos guardrails |
| main.tf → `locals.log_alerts` | Eventos que alertan | Según tu modelo de amenazas |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
 PREVENTIVOS                          DETECTIVOS                              RESPUESTA
 IAM Deny Policy:                      Audit logs (Admin + Data Access)  ─►    Alertas basadas en logs:
  · serviceAccountKeys.create/upload    ├─ sink → Log bucket 365 d          · roles/owner otorgado
  · (opcional) sinks/buckets delete     │       (Log Analytics, lock opc.)  · llave de SA creada
 RBAC: developer · sre · auditor ·      └─ sink → GCS CMEK (Nearline 30 d,  · cambios de auditoría/sinks
       finops + rol custom deployer             retención 365 d)            · firewall 0.0.0.0/0
 Break-glass: owner con IAM Condition   SCC → Pub/Sub (opcional, org)       → email (rate limit 5 min)
   request.time < break_glass_until     VPC-SC dry-run (opcional)
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `google_project_iam_audit_config` | Data Access para servicios sensibles |
| `google_logging_project_bucket_config` + sinks | Retención, Log Analytics, archivo GCS con CMEK |
| `google_monitoring_alert_policy.log_alerts` | `condition_matched_log` con rate limit |
| `google_iam_deny_policy.guardrails` | Niega permisos a todos salvo excepciones |
| `google_project_iam_custom_role.deployer` + `google_project_iam_member.rbac` | RBAC por equipo |
| `google_project_iam_member.break_glass` | Owner con caducidad automática |
| SCC / VPC-SC (`count`) | Solo con organización / access policy |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `data_access_audit_services` | 4 servicios | Costo por volumen |
| `log_retention_days` | 365 |  |
| `lock_log_bucket` | `false` | IRREVERSIBLE |
| `protect_audit_sinks` | `false` | Requiere excepciones |
| `deny_exception_principals` | `[]` | Formato `principal://...` |
| `rbac_members` | `{}` | Por equipo |
| `break_glass_until` | `null` | RFC 3339 |
| `org_id` / `access_policy_id` | `null` | Opcionales |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd 06-terraform-gcp
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del micro lab 00>   # no aplica al micro lab 00
cp microlabs/11-security-iam-deny-rbac/terraform.tfvars.example microlabs/11-security-iam-deny-rbac/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  11-security-iam-deny-rbac
bash scripts/lab.sh apply 11-security-iam-deny-rbac
bash scripts/lab.sh test  11-security-iam-deny-rbac
bash scripts/lab.sh destroy 11-security-iam-deny-rbac
```

Las IAM Deny Policies se evalúan **antes** que los permisos: ni siquiera un Owner puede crear llaves de SA si no está en las excepciones.

## Prueba automatizada (`scripts/smoke-test.sh`)

Data Access configurado; log bucket con 365 días y Analytics; 2 sinks; archivo con CMEK; **prueba negativa**: crear una llave para la SA probe → `PERMISSION_DENIED`; un evento auditado llega al log bucket; alertas creadas; el rol custom no incluye `setIamPolicy`.

### Resultado esperado (extracto)

```
== Auditoría
  OK   Retención del log bucket (días) (365)
  OK   Sinks de auditoría (2)
  OK   Archivo GCS cifrado con CMEK
== IAM Deny Policy (prueba negativa)
  OK   Creación de llave denegada
== Evento auditado llega al log bucket
  OK   Audit logs recientes en el bucket
SMOKE TEST OK  (10 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `GCP11_TFVARS` | File | Aplícalo antes que los demás labs |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `destroy` falla al borrar sinks | Activaste `protect_audit_sinks`: agrega tu identidad a `deny_exception_principals`, aplica y luego destruye. |
| `Role ... already exists` (custom role) | Los roles borrados quedan 7 días reservados; `gcloud iam roles undelete` o cambia `environment`. |
| El sink a GCS no escribe | La `writer_identity` necesita `objectCreator` (incluido) y el agente de GCS acceso a la CMEK (incluido). |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Log Analytics; alertas accionables |
| Seguridad | Deny policies, RBAC mínimo, break-glass con caducidad, CMEK |
| Confiabilidad | Doble destino de auditoría |
| Rendimiento | N/A |
| Costos | Data Access solo donde importa; Nearline a 30 días |
| Sostenibilidad | Retención acotada |

## Storage mínimo

| Recurso | Definición |
|---|---|
| Log bucket | 365 días (primeros 30 incluidos en el precio de ingesta) |
| GCS archivo | Nearline a 30 días; retención 365 |

**Costo aproximado:** Bajo: ingesta de logs (50 GiB/mes gratis) + almacenamiento.
