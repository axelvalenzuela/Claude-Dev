# Micro lab 05 (GCP): Arquitectura web de 3 niveles (Load Balancer + MIG + Cloud SQL HA)

> **Objetivo:** Arquitectura de referencia: LB global con Cloud Armor, MIG regional sin IPs públicas con autohealing, y Cloud SQL PostgreSQL HA por IP privada con TLS y Secret Manager.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~20 min · **Costo si queda encendido:** ~USD 120/mes ⚠️ destruir al terminar

**Prerrequisitos**

- Lab 00
- Presupuesto: ~USD 4/día

**1. Prepara las variables**

```bash
cd 03-cloud-e-infraestructura/lab11-terraform-gcp
cp microlabs/05-web3tier-lb-mig-cloudsql/terraform.tfvars.example microlabs/05-web3tier-lb-mig-cloudsql/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `db_high_availability` | `false` para ahorrar |
| `domain` | opcional, HTTPS |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  05-web3tier-lb-mig-cloudsql
bash scripts/lab.sh plan  05-web3tier-lb-mig-cloudsql   # revisa qué se crea
bash scripts/lab.sh apply 05-web3tier-lb-mig-cloudsql
```

**3. Después del apply**

- El LB tarda 5-8 min en responder la primera vez
- `curl $(terraform -chdir=microlabs/05-web3tier-lb-mig-cloudsql output -raw app_url)/db`

**4. Verifica**

```bash
bash scripts/lab.sh test 05-web3tier-lb-mig-cloudsql   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 05-web3tier-lb-mig-cloudsql
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| startup.sh.tpl | Tu aplicación (o imagen personalizada) | Siempre en un proyecto real |
| main.tf → `google_compute_security_policy.waf` | Reglas OWASP, sensibilidad, rate limit | Falsos positivos o nuevos ataques |
| main.tf → `google_sql_database_instance.db.settings` | Tier, HA, flags, backups | Carga real |
| variables.tf → `domain` | HTTPS administrado | En cuanto tengas dominio |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
Internet ─► IP global ─► External Application LB (EXTERNAL_MANAGED)
                          └─ Cloud Armor: SQLi, XSS, rate_based_ban 300/min por IP
                                  ▼
                 Backend service ─► MIG REGIONAL (2–4 VMs e2-small en varias zonas)
                                    · sin IP pública (salida por Cloud NAT) · OS Login · Shielded VM
                                    · autohealing (health check /health) · update PROACTIVE sin caída
                                    · app systemd: /, /health, /db
                                  ▼ IP privada (Private Service Access), TLS ENCRYPTED_ONLY
                 Cloud SQL PostgreSQL 16 HA (REGIONAL) · PITR · backups 7 · Query Insights
                 contraseña: Secret Manager (leída por la VM con su SA, sin llaves)
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `module.vpc` | Subnet app, Cloud NAT, PSA, firewall deny-all + health checks + IAP |
| `google_sql_database_instance.db` | `availability_type = REGIONAL`, `ipv4_enabled = false`, `ssl_mode = ENCRYPTED_ONLY` |
| `google_secret_manager_secret` + `random_password` | Credencial generada y almacenada; la VM la lee vía REST |
| `google_compute_instance_template` + `startup.sh.tpl` | Debian 12, app Python stdlib, Shielded VM |
| `google_compute_region_instance_group_manager` + autoscaler | Autohealing, rolling proactivo, CPU 60 % |
| `google_compute_security_policy.waf` | Reglas preconfiguradas OWASP + rate limit |
| Backend / URL map / proxy / forwarding rule | HTTP; HTTPS opcional con certificado administrado (`domain`) |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `machine_type` | e2-small |  |
| `min_replicas` / `max_replicas` | 2 / 4 |  |
| `db_tier` | db-custom-1-3840 |  |
| `db_high_availability` | `true` | `false` ahorra ~50 % |
| `rate_limit_per_minute` | 300 | Cloud Armor |
| `domain` | `null` | HTTPS administrado |
| `deletion_protection` | `false` | `true` en prod |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd 03-cloud-e-infraestructura/lab11-terraform-gcp
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/05-web3tier-lb-mig-cloudsql/terraform.tfvars.example microlabs/05-web3tier-lb-mig-cloudsql/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  05-web3tier-lb-mig-cloudsql
bash scripts/lab.sh apply 05-web3tier-lb-mig-cloudsql
bash scripts/lab.sh test  05-web3tier-lb-mig-cloudsql
bash scripts/lab.sh destroy 05-web3tier-lb-mig-cloudsql
```

Conexión administrativa sin IP pública: `gcloud compute ssh <vm> --tunnel-through-iap`, y luego `journalctl -u lab11-app -f`.

## Prueba automatizada (`scripts/smoke-test.sh`)

LB responde (5-8 min la primera vez); 2 backends sanos; respuestas desde **2 zonas**; VMs sin IP pública; `/db` ok por **TLS**; Cloud SQL `REGIONAL`, sin IP pública y con PITR; Cloud Armor bloquea **SQLi y XSS** (403). `CHAOS=1` borra una VM y mide la recuperación.

### Resultado esperado (extracto)

```
== Capa web: Load Balancer (http://34.120.x.x)
  OK   Backends sanos (2)
== Capa app: MIG regional
  OK   Respuestas desde 2 zonas (us-central1-a us-central1-c)
  OK   VMs con IP pública (0)
== Capa datos: Cloud SQL
  OK   Conexión TLS (ssl_mode ENCRYPTED_ONLY) (true)
  OK   Alta disponibilidad (REGIONAL)
== Cloud Armor
  OK   SQL injection bloqueada (403)
SMOKE TEST OK  (13 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `LAB05_TFVARS` | File | job con `timeout: 1h` (Cloud SQL HA tarda) |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| Backends `UNHEALTHY` | El startup script tarda en instalar paquetes (2-3 min); revisa `gcloud compute instances get-serial-port-output`. Sin NAT no hay apt. |
| `/db` → 500 de Secret Manager | La SA de la VM necesita `secretAccessor` sobre el secreto (incluido); revisa el scope `cloud-platform`. |
| Cloud SQL tarda > 15 min | Normal en HA con PSA nuevo; el peering de Service Networking se crea primero. |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Rolling updates proactivos; Query Insights; logs del LB |
| Seguridad | Cloud Armor; sin IPs públicas; OS Login; TLS; Secret Manager |
| Confiabilidad | MIG regional + autohealing; SQL HA + PITR |
| Rendimiento | LB global; autoscaling por CPU |
| Costos | e2-small; HA opcional; destruir al terminar |
| Sostenibilidad | Escala con la demanda |

## Storage mínimo

| Recurso | Definición |
|---|---|
| Disco VM | 10 GB pd-balanced por VM |
| Cloud SQL | 10 GB SSD (mínimo) con autoresize; backups 7; logs de transacciones 7 días |

**Costo aproximado:** ~USD 120/mes con HA encendido (SQL HA ~70, VMs ~25, LB ~18, NAT). **Destruye al terminar.**
