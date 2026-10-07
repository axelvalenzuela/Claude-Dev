# Micro lab 10: AWS CloudFormation StackSets (baseline multi-cuenta y multi-región)

> **Objetivo:** gobernar muchas cuentas desde un solo punto. Terraform administra un **StackSet** que despliega un template de CloudFormation (baseline de seguridad) en todas las cuentas de las OUs destino, con auto-deployment para las cuentas nuevas y un **bus de eventos central** que concentra los hallazgos de seguridad.

## Arquitectura

```
          Cuenta management / delegated admin
 ┌───────────────────────────────────────────────────────────┐
 │ Terraform ─► StackSet "security-baseline" (SERVICE_MANAGED)│
 │              auto_deployment · managed_execution           │
 │              25 % concurrencia · 10 % tolerancia a fallas  │
 │ EventBridge bus "security-central" (aws:PrincipalOrgID) ──►│── SNS ─► equipo de seguridad
 └────────────┬──────────────────────────────▲───────────────┘
              │ stack instances              │ PutEvents (root, GuardDuty ≥7,
              ▼ (OU × regiones)              │  Security Hub HIGH, cambios IAM)
   ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
   │ Cuenta Dev       │ │ Cuenta Test      │ │ Cuenta Prod      │
   │ rol audit (MFA)  │ │ rol audit (MFA)  │ │ rol audit (MFA)  │
   │ reglas EB → hub  │ │ reglas EB → hub  │ │ reglas EB → hub  │
   │ Config rules*    │ │ Config rules*    │ │ Config rules*    │
   └──────────────────┘ └──────────────────┘ └──────────────────┘
```

## Prerrequisitos (una vez, en la cuenta de management)

```bash
# 1. Habilitar trusted access de StackSets con Organizations
aws cloudformation activate-organizations-access
# 2. (Recomendado) delegar la administración a una cuenta de plataforma/seguridad
aws organizations register-delegated-administrator \
  --service-principal member.org.stacksets.cloudformation.amazonaws.com --account-id <cuenta-plataforma>
# 3. Datos para tfvars
aws organizations describe-organization --query Organization.Id
aws organizations list-organizational-units-for-parent --parent-id <root-id>
```

> Con SERVICE_MANAGED el StackSet **no** se despliega en la cuenta de management. Si no tienes Organizations, usa `permission_model = "SELF_MANAGED"` y despliega `templates/stackset-execution-role.yaml` en cada cuenta destino.

## Templates

| Archivo | Contenido |
|---|---|
| `templates/security-baseline.yaml` | Rol de auditoría con MFA, reglas EventBridge (root, findings, IAM) hacia el bus central, Config rules condicionales |
| `templates/stackset-execution-role.yaml` | Rol de ejecución para el modo SELF_MANAGED |

**Cómo versionar el baseline:** edita el YAML, sube `baseline_version` y haz un MR. El plan muestra la actualización del StackSet y CloudFormation la propaga con las preferencias de operación configuradas.

## Pruebas

1. `terraform apply` y luego `aws cloudformation list-stack-instances --stack-set-name lab10-dev-stacksets-security-baseline`.
2. Inicia sesión como root en una cuenta miembro de prueba: debe llegar un correo del hub.
3. Mueve una cuenta nueva a la OU: el baseline se instala solo (auto-deployment).
4. Detección de drift: `aws cloudformation detect-stack-set-drift --stack-set-name ...`.

## Parámetros

| Variable | Default | Descripción |
|---|---|---|
| `permission_model` | SERVICE_MANAGED | |
| `call_as` | SELF | DELEGATED_ADMIN desde la cuenta delegada |
| `organization_id` | (requerido) | |
| `target_ou_ids` / `target_account_ids` | | Destinos |
| `target_regions` | us-east-1, us-west-2 | |
| `audit_account_id` | esta cuenta | |
| `enable_config_rules` | `false` | Requiere recorder (lab 11) |
| `max_concurrent_percentage` / `failure_tolerance_percentage` | 25 / 10 | Despliegue gradual |

### Parámetros en GitLab

`LAB10_TFVARS` (File). El job de este lab debe usar un rol creado **en la cuenta management o delegada** (`AWS_APPLY_ROLE_ARN_ORG`), separado del rol de las cuentas de workload.

<!-- detalle-funcional -->
## Ejecución rápida

```bash
cd lab10
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/10-cloudformation-stacksets/terraform.tfvars.example microlabs/10-cloudformation-stacksets/terraform.tfvars   # edita owner y demás
bash scripts/lab.sh init  10-cloudformation-stacksets
bash scripts/lab.sh apply 10-cloudformation-stacksets
bash scripts/lab.sh test  10-cloudformation-stacksets      # smoke test automatizado (abajo)
bash scripts/lab.sh destroy 10-cloudformation-stacksets
```

Con `make`: `make apply LAB=10-cloudformation-stacksets` · `make test LAB=10-cloudformation-stacksets`. Requisitos del smoke test: AWS CLI v2, `jq`, `curl` y credenciales con permisos de escritura sobre el lab.

## Prueba automatizada (`scripts/smoke-test.sh`)

Verifica que el StackSet esté `ACTIVE` y que todas las instancias (cuenta × región) estén en `SUCCEEDED`, lanza una **detección de drift** y espera `IN_SYNC`, y comprueba que el bus central restringe a la organización. Con `SEND_TEST_EVENT=1` publica un evento en el bus y debe llegar un correo.

Para cuentas delegadas: `CALL_AS=DELEGATED_ADMIN bash scripts/lab.sh test 10-cloudformation-stacksets`.

### Práctica de drift

1. Asume `OrganizationAccountAccessRole` en una cuenta miembro y borra la regla `RootActivityRule`.
2. Corre el smoke test: el drift aparece como `DRIFTED`.
3. Corrige con un apply (o con *Update StackSet* sin cambios) y verifica `IN_SYNC` otra vez.

### Resultado esperado (extracto)

```
== StackSet lab10-dev-stacksets-security-baseline
  OK   Estado (ACTIVE)
  ..   Instancias: 6 (cuentas x regiones)
  ..   111122223333 us-east-1: SUCCEEDED
  OK   Instancias en SUCCEEDED (6)
== Drift
  OK   Drift del baseline (IN_SYNC)
SMOKE TEST OK  (6 verificaciones)
```

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `ValidationError: You must enable organizations access` | Ejecuta `aws cloudformation activate-organizations-access` en la cuenta de management. |
| Instancias en `OUTDATED` / `FAILED` | Revisa `StatusReason`; lo común es un nombre IAM que ya existe (`lab10-security-audit`) o una región deshabilitada en la cuenta. |
| Las cuentas no reenvían eventos | La regla cross-region/cross-account necesita que el bus central permita `events:PutEvents` con `aws:PrincipalOrgID` y que el rol `ForwardToCentralBusRole` exista. |
<!-- detalle-funcional -->

## Well-Architected (Management & Governance Lens)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Baseline versionado; despliegue gradual; managed execution; detección de drift |
| Seguridad | Guardrails idénticos en todas las cuentas; auditoría centralizada; bus limitado a la organización |
| Confiabilidad | Tolerancia a fallas y concurrencia controladas; auto-deployment |
| Eficiencia de rendimiento | Despliegue paralelo por región |
| Optimización de costos | Sin costo de StackSets; reglas de Config opcionales (cobro por evaluación) |
| Sostenibilidad | Un solo template para N cuentas |

## Storage mínimo

No usa storage; los templates viven en Git y CloudFormation guarda la versión desplegada.
