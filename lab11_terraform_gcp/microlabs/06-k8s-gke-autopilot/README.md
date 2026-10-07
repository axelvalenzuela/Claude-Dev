# Micro lab 06 (GCP): GKE Autopilot privado con workload endurecido

> **Objetivo:** Operar Kubernetes administrado con seguridad por defecto: nodos privados, Workload Identity, Pod Security `restricted`, NetworkPolicy, HPA y PDB, todo con Terraform.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~12 min · **Costo si queda encendido:** ~USD 95/mes ⚠️ destruir al terminar

**Prerrequisitos**

- Lab 00
- `kubectl` + `gke-gcloud-auth-plugin`

**1. Prepara las variables**

```bash
cd lab11_terraform_gcp
cp microlabs/06-k8s-gke-autopilot/terraform.tfvars.example microlabs/06-k8s-gke-autopilot/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `authorized_networks` | tu IP: `curl ifconfig.me`/32 |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  06-k8s-gke-autopilot
bash scripts/lab.sh plan  06-k8s-gke-autopilot   # revisa qué se crea
bash scripts/lab.sh apply 06-k8s-gke-autopilot
```

**3. Después del apply**

- Si falla la primera vez al crear objetos de Kubernetes, repite `apply`
- `$(terraform -chdir=microlabs/06-k8s-gke-autopilot output -raw get_credentials)`

**4. Verifica**

```bash
bash scripts/lab.sh test 06-k8s-gke-autopilot   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 06-k8s-gke-autopilot
```
<!-- despliegue -->


## Arquitectura

```
kubectl (authorized_networks) ─► control plane público restringido
VPC lab11-dev-gke: subnet nodes + rangos secundarios pods/services · Cloud NAT
GKE Autopilot regional (nodos privados, Dataplane V2, release channel REGULAR)
  └─ namespace lab11-app  [pod-security: restricted]
       ├─ SA app ──Workload Identity──► GSA lab11-dev-gke-app (logWriter, metricWriter)
       ├─ Deployment web (nginx-unprivileged, non-root, read-only rootfs, drop ALL, probes, topology spread)
       ├─ Service LoadBalancer :80 → 8080
       ├─ HPA 2–6 (CPU 60 %) · PDB minAvailable 1
       └─ NetworkPolicy: default-deny + allow 8080
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `google_container_cluster` | `enable_autopilot`, nodos privados, `master_authorized_networks`, ventana de mantenimiento |
| `google_service_account_iam_member.workload_identity` | KSA `lab11-app/app` → GSA |
| `provider "kubernetes"` | Credenciales del cluster recién creado (token de `google_client_config`) |
| `kubernetes_deployment_v1` / `_service_v1` / HPA / PDB / NetworkPolicy | Workload completo como código |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `authorized_networks` | `0.0.0.0/0` | Pon tu IP /32 |
| `image` | nginx-unprivileged | Debe ser non-root en 8080 |
| `min_replicas` / `max_replicas` | 2 / 6 | HPA |
| `nodes_cidr`, `pods_cidr`, `services_cidr` | 10.60/22, 10.64/14, 10.68/20 |  |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd lab11_terraform_gcp
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/06-k8s-gke-autopilot/terraform.tfvars.example microlabs/06-k8s-gke-autopilot/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  06-k8s-gke-autopilot
bash scripts/lab.sh apply 06-k8s-gke-autopilot
bash scripts/lab.sh test  06-k8s-gke-autopilot
bash scripts/lab.sh destroy 06-k8s-gke-autopilot
```

Si el primer apply falla al crear objetos de Kubernetes (cluster recién creado), repite `apply`: el provider ya tendrá endpoint y credenciales.

## Prueba automatizada (`scripts/smoke-test.sh`)

Autopilot + nodos privados + workload pool; rollout disponible; pods non-root; un **pod privilegiado es rechazado** por PSA restricted; LoadBalancer con IP y HTTP 200; PDB y 2 NetworkPolicies. `LOAD=1` genera carga para ver el HPA.

### Resultado esperado (extracto)

```
== Cluster lab11-dev-gke
  OK   Nodos privados (true)
  OK   Workload Identity (mi-proyecto.svc.id.goog)
== Pod Security Admission (restricted)
  OK   Pod privilegiado rechazado por la política restricted
== Servicio público
  OK   HTTP 200 en http://34.x.x.x
SMOKE TEST OK  (10 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `LAB06_TFVARS` | File | terraform.tfvars |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `kubectl` timeout | Tu IP no está en `authorized_networks`. |
| Pods `Pending` varios minutos | Autopilot aprovisiona nodos bajo demanda (1-3 min). |
| `CreateContainerConfigError: runAsNonRoot` | La imagen corre como root; usa una imagen non-root numérica. |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Workload declarativo en Terraform; release channel |
| Seguridad | Nodos privados, WI, PSA restricted, NetworkPolicy |
| Confiabilidad | Regional, topology spread, PDB, probes |
| Rendimiento | HPA por CPU |
| Costos | Autopilot cobra por pod solicitado |
| Sostenibilidad | Bin packing administrado |

## Storage mínimo

| Recurso | Definición |
|---|---|
| Pods | `emptyDir` para /tmp; sin volúmenes persistentes |

**Costo aproximado:** ~USD 75/mes de fee del cluster + pods (~USD 20). **Destruye al terminar.**
