# Micro lab 11: Seguridad y gobernanza (detectivos, preventivos, RBAC/ABAC y SCPs)

> **Objetivo:** aplicar en una cuenta los controles mínimos del pilar de Seguridad: registrar todo, detectar amenazas, medir el cumplimiento (CIS / FSBP), prevenir configuraciones inseguras y definir el acceso por roles (RBAC) y por atributos (ABAC).

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~3 min · **Costo si queda encendido:** ~USD 5-20/mes

**Prerrequisitos**

- Lab 00
- Aplícalo **antes** que los demás labs

**1. Prepara las variables**

```bash
cd lab10_terraform_aws
cp microlabs/11-security-guardrails-rbac/terraform.tfvars.example microlabs/11-security-guardrails-rbac/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `owner` | tu correo |
| `security_emails` | recibe hallazgos |
| `manage_scps` | `true` solo en la cuenta management |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  11-security-guardrails-rbac
bash scripts/lab.sh plan  11-security-guardrails-rbac   # revisa qué se crea
bash scripts/lab.sh apply 11-security-guardrails-rbac
```

**3. Después del apply**

- Confirma la suscripción SNS
- Revisa Security Hub después de 24 h

**4. Verifica**

```bash
bash scripts/lab.sh test 11-security-guardrails-rbac   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 11-security-guardrails-rbac
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| variables.tf → `rbac_roles` | Roles por función, políticas, duración, boundary | Según tus equipos |
| policies/developer-boundary.json | Techo de permisos del developer | Al habilitar nuevos servicios |
| policies/abac-ec2-team.json | Etiqueta usada para ABAC (`Team`) | Otro criterio de aislamiento |
| policies/scp/*.json | SCPs (regiones, cifrado, root) | Solo en management; probar en sandbox |
| variables.tf → `config_managed_rules` | Reglas de AWS Config | Según el estándar de cumplimiento |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
 PREVENTIVOS                         DETECTIVOS                          RESPUESTA
 ┌─────────────────────────┐   ┌──────────────────────────────┐   ┌────────────────────────┐
 │ SCPs (Organizations)    │   │ CloudTrail multi-región       │   │ EventBridge rule        │
 │ Password policy         │   │   + validación de integridad  │──►│ GuardDuty sev>=7        │
 │ S3 Block Public (cuenta)│   │ AWS Config + 14 reglas        │   │ Security Hub HIGH/CRIT  │
 │ EBS cifrado por defecto │   │ GuardDuty (+S3, EBS, Lambda,  │   │ uso de break-glass      │
 │ Permissions boundary    │   │   RDS)                        │   │        │                │
 │ Roles RBAC con MFA      │   │ Security Hub FSBP + CIS 3.0   │   │        ▼                │
 │ ABAC por etiqueta Team  │   │ IAM Access Analyzer           │   │ SNS (KMS) → email/Slack │
 └─────────────────────────┘   └──────────────┬───────────────┘   └────────────────────────┘
                                              ▼
                          S3 audit (KMS, versionado, IA a 30 días, expira a 365 días)
```

## Modelo RBAC incluido

| Rol | Permisos | Sesión | Controles |
|---|---|---|---|
| `break-glass-admin` | AdministratorAccess | 1 h | MFA reciente (< 1 h) y alerta en cada uso |
| `platform-engineer` | PowerUser + IAM read | 4 h | MFA |
| `developer` | PowerUser ∩ **boundary** + ABAC | 8 h | Solo crea roles `lab10-*` con boundary; tamaños t*/db.t*; no toca servicios de seguridad |
| `auditor` | SecurityAudit + ViewOnly | 4 h | MFA |
| `finops` | Billing + Budgets RO | 4 h | MFA |

**ABAC** (`policies/abac-ec2-team.json`): un developer con la etiqueta de sesión `Team=payments` solo puede arrancar, detener o abrir sesión SSM en instancias con `Team=payments`, y está obligado a etiquetar lo que crea.

**SCPs** (`policies/scp/`): evitan salir de la organización o apagar servicios de seguridad, restringen regiones, exigen cifrado e IMDSv2 y bloquean el usuario root. Pruébalas siempre primero en una OU *sandbox*.

## Pasos

```bash
terraform apply
# Probar RBAC (requiere MFA en tu identidad):
aws sts assume-role --role-arn <rbac_role_arns.auditor> --role-session-name test \
  --serial-number <mfa-arn> --token-code 123456
# Generar un hallazgo de muestra:
aws guardduty create-sample-findings --detector-id $(terraform output -raw guardduty_detector_id) \
  --finding-types "UnauthorizedAccess:EC2/SSHBruteForce"
```

Revisa el *score* de Security Hub después de 24 h y corrige los controles fallidos de los labs 01 a 08.

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `audit_log_retention_days` | 365 | |
| `record_global_resources` | `true` | Solo en una región |
| `config_recording_frequency` | DAILY | CONTINUOUS en producción |
| `config_managed_rules` | 14 reglas | mapa regla → parámetros |
| `guardduty_features` | S3, EBS, Lambda, RDS | |
| `securityhub_standards` | FSBP, CIS 3.0 | |
| `rbac_roles` | 5 roles | Personalizable |
| `manage_scps` / `scp_target_ids` | `false` / `[]` | Solo en management |

GitLab: `LAB11_TFVARS` (File). Aplícalo **antes** que los demás labs para que todo quede auditado.

<!-- detalle-funcional -->
## Ejecución rápida

```bash
cd lab10_terraform_aws
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/11-security-guardrails-rbac/terraform.tfvars.example microlabs/11-security-guardrails-rbac/terraform.tfvars   # edita owner y demás
bash scripts/lab.sh init  11-security-guardrails-rbac
bash scripts/lab.sh apply 11-security-guardrails-rbac
bash scripts/lab.sh test  11-security-guardrails-rbac      # smoke test automatizado (abajo)
bash scripts/lab.sh destroy 11-security-guardrails-rbac
```

Con `make`: `make apply LAB=11-security-guardrails-rbac` · `make test LAB=11-security-guardrails-rbac`. Requisitos del smoke test: AWS CLI v2, `jq`, `curl` y credenciales con permisos de escritura sobre el lab.

## Prueba automatizada (`scripts/smoke-test.sh`)

Comprueba los controles **detectivos** (CloudTrail con validación, Config grabando, GuardDuty, Security Hub con 2 estándares y Access Analyzer) y los **preventivos** (EBS cifrado, S3 BPA de cuenta y password policy). Además **simula** permisos RBAC con `iam simulate-principal-policy`, sin asumir roles: developer puede `lambda:CreateFunction`, pero `cloudtrail:StopLogging` e `iam:CreateUser` quedan en `explicitDeny` por el boundary; auditor no puede escribir en S3. Por último genera un hallazgo de muestra de GuardDuty que debe llegar por correo.

### Resultado esperado (extracto)

```
== Detectivos
  OK   CloudTrail registrando (True)
  OK   AWS Config grabando (True)
  OK   GuardDuty (ENABLED)
  OK   Security Hub: estándares habilitados (2)
== RBAC (simulación de políticas, no requiere asumir roles)
  OK   developer: lambda:CreateFunction (allowed)
  OK   developer: cloudtrail:StopLogging (boundary) (explicitDeny)
  OK   developer: iam:CreateUser (boundary) (explicitDeny)
  OK   auditor: s3:PutObject (implicitDeny)
SMOKE TEST OK  (17 verificaciones)
```

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `MaxNumberOfConfigurationRecordersExceededException` | Ya hay un recorder (Control Tower u otro). Impórtalo o desactiva esa parte del lab. |
| `InvalidAccessException` en Security Hub | La cuenta ya está administrada por un administrador delegado; los estándares se gestionan desde esa cuenta. |
| CloudTrail `InsufficientS3BucketPolicyException` | La política del bucket condiciona `aws:SourceArn` al nombre exacto del trail y a la región de `aws_region`. |
| Las SCPs bloquean al propio pipeline | Aplícalas primero a una OU *sandbox*; la excepción `OrganizationAccountAccessRole` permite recuperar el acceso. |
<!-- detalle-funcional -->

## Well-Architected (pilar de Seguridad)

| Área SEC | Implementación |
|---|---|
| Fundamentos de seguridad | SCPs, boundary, gobierno multi-cuenta (lab 10) |
| Gestión de identidades y accesos | RBAC con MFA, sesiones cortas, ABAC, sin usuarios IAM |
| Detección | CloudTrail, Config, GuardDuty, Security Hub, Access Analyzer |
| Protección de infraestructura | IMDSv2, SSH deshabilitado, flow logs (reglas de Config) |
| Protección de datos | KMS, EBS por defecto, S3 BPA, TLS-only |
| Respuesta a incidentes | EventBridge → SNS; alerta de break-glass; logs inmutables con validación |

## Storage mínimo

| Recurso | Definición |
|---|---|
| S3 audit | Standard → Standard-IA a 30 días → expira a 365 días; versionado |
| Config | Snapshots diarios |

**Costo:** GuardDuty y Security Hub cobran por volumen (30 días de prueba); Config cobra por ítem registrado y por evaluación (DAILY lo reduce).
