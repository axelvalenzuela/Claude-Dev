# Micro lab 10 (GCP): Gobernanza de organización: carpetas, Org Policies, tags y fábrica de proyectos

> **Objetivo:** El equivalente de StackSets + SCPs en GCP: guardrails preventivos heredados por carpeta y una fábrica que crea N proyectos con el mismo baseline.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~5 min · **Costo si queda encendido:** USD 0

**Prerrequisitos**

- **Organización** de Google Cloud
- Roles: Folder Admin, Org Policy Admin, Tag Admin, Project Creator, Billing User

**1. Prepara las variables**

```bash
cd lab11_terraform_gcp
cp microlabs/10-governance-org-policies/terraform.tfvars.example microlabs/10-governance-org-policies/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `org_id` | `gcloud organizations list` |
| `parent_folder_id` | carpeta sandbox |
| `billing_account` | para los proyectos |
| `project_suffix` | único, p. ej. tus iniciales + año |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  10-governance-org-policies
bash scripts/lab.sh plan  10-governance-org-policies   # revisa qué se crea
bash scripts/lab.sh apply 10-governance-org-policies
```

**3. Después del apply**

- Revisa las políticas efectivas: `gcloud org-policies list --project <proyecto>`

**4. Verifica**

```bash
bash scripts/lab.sh test 10-governance-org-policies   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 10-governance-org-policies
```
<!-- despliegue -->


## Arquitectura

```
Organización
  └─ carpeta sandbox (parent_folder_id)
       └─ lab11-dev  ◄── Org Policies: sin llaves de SA, sin IPs externas, UBLA, PAP, OS Login,
          │                SQL sin IP pública, ubicaciones in:us-locations, restrictServiceUsage (condicional por tag)
          │           ◄── Firewall jerárquico: allow IAP 22/3389, deny 22/3389 desde Internet
          ├─ dev   [tag lab11-environment=dev]  ─► proyecto ventas-dev-<sufijo>
          └─ prod  [tag lab11-environment=prod] ─► proyecto ventas-prod-<sufijo>
Cada proyecto (module project-baseline): sin red default, APIs base, audit logs, operadores, budget
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `google_folder` root + env | Jerarquía del lab |
| `google_org_policy_policy` (boolean, list, condicional) | Guardrails heredados |
| `google_tags_tag_key/value/binding` | Tags para condicionar políticas |
| `google_compute_firewall_policy` + rules + association | Firewall que los proyectos no pueden relajar |
| `module.projects` (`modules/project-baseline`) | Fábrica: `for_each` sobre `var.projects` |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `org_id` | — | `gcloud organizations list` |
| `parent_folder_id` | `null` | Carpeta sandbox recomendada |
| `billing_account` | — |  |
| `allowed_locations` | `in:us-locations` |  |
| `project_suffix` | — | Unicidad global |
| `projects` | ventas-dev, ventas-prod | Mapa de proyectos |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd lab11_terraform_gcp
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/10-governance-org-policies/terraform.tfvars.example microlabs/10-governance-org-policies/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  10-governance-org-policies
bash scripts/lab.sh apply 10-governance-org-policies
bash scripts/lab.sh test  10-governance-org-policies
bash scripts/lab.sh destroy 10-governance-org-policies
```

Requiere una identidad con: Folder Admin, Organization Policy Administrator, Tag Admin, Compute Organization Firewall Policy Admin, Project Creator y Billing Account User. Prueba siempre en una carpeta **sandbox**.

## Prueba automatizada (`scripts/smoke-test.sh`)

2 carpetas de entorno; políticas **efectivas** (`--effective`) en cada proyecto; proyectos sin red default y con auditoría de datos; **prueba negativa**: crear una llave de SA debe fallar; regla deny en el firewall jerárquico.

### Resultado esperado (extracto)

```
== Org policies efectivas (heredadas por cada proyecto)
  OK   ventas-dev-av26 · iam.disableServiceAccountKeyCreation
  OK   ventas-dev-av26 · compute.vmExternalIpAccess
== Pruebas negativas (deben fallar por política)
  OK   Creación de llave JSON bloqueada (iam.disableServiceAccountKeyCreation)
SMOKE TEST OK  (14 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `LAB10_TFVARS` | File | Usa un SA de apply con permisos a nivel de org (separado del de proyecto) |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `Error 403 orgpolicy.policies.create` | Te falta *Organization Policy Administrator* en la carpeta u organización. |
| `project_id already exists` | Los IDs son globales y se reservan 30 días tras borrarse; cambia `project_suffix`. |
| La política condicional por tag no aplica | Los tags tardan unos minutos en propagarse; verifica `gcloud resource-manager tags bindings list`. |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Baseline idéntico por proyecto; jerarquía como código |
| Seguridad | Guardrails preventivos heredados; firewall jerárquico |
| Confiabilidad | Proyectos aislados por entorno |
| Rendimiento | N/A |
| Costos | Budget por proyecto; servicios restringidos en prod |
| Sostenibilidad | Ubicaciones restringidas |

## Storage mínimo

| Recurso | Definición |
|---|---|
| — | No crea storage |

**Costo aproximado:** Sin costo (gobernanza y proyectos vacíos).
