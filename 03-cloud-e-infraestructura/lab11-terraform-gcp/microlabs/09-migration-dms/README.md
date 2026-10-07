# Micro lab 09 (GCP): Migración de bases de datos con Database Migration Service

> **Objetivo:** Migrar PostgreSQL a Cloud SQL con **DMS en modo continuo** (dump + CDC), con un origen "on-prem" simulado, conectividad privada y cutover controlado.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~15 min · **Costo si queda encendido:** ~USD 2/día ⚠️ destruir al terminar

**Prerrequisitos**

- Lab 00
- Presupuesto: ~USD 2/día

**1. Prepara las variables**

```bash
cd 03-cloud-e-infraestructura/lab11-terraform-gcp
cp microlabs/09-migration-dms/terraform.tfvars.example microlabs/09-migration-dms/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `create_demo_source` | `true` (VM de origen simulada) |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  09-migration-dms
bash scripts/lab.sh plan  09-migration-dms   # revisa qué se crea
bash scripts/lab.sh apply 09-migration-dms
```

**3. Después del apply**

- Espera ~6 min al startup del origen
- `bash microlabs/09-migration-dms/scripts/migrate.sh verify`, luego `start`, `status` y `promote`

**4. Verifica**

```bash
bash scripts/lab.sh test 09-migration-dms   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 09-migration-dms
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| variables.tf → `create_demo_source`, `source_host` | Origen real vs simulado | Para migrar tu BD |
| source-startup.sh.tpl | Datos de ejemplo | Para simular tu esquema |
| main.tf → `connection_profile.destination.cloudsql.settings` | Tier, disco, versión destino | Según tamaño |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
VPC lab11-dev-dms (simula la red corporativa conectada por VPN/Interconnect)
  └─ VM onprem-pg (Debian 12, PostgreSQL 15 + pglogical, sin IP pública, OS Login)
       · base ventas: clientes (500) y pedidos (5000), todas con PK
       · usuario migration (REPLICATION) con contraseña en Secret Manager
                      │ VPC peering (Private Service Access)
                      ▼
Database Migration Service: job CONTINUOUS
  · perfil origen (postgresql host/puerto/usuario)
  · perfil destino (cloudsql: DMS crea la instancia POSTGRES_15, solo IP privada)
  verify → start (full dump → CDC) → validar → promote (CUTOVER) → la réplica pasa a primaria
```

## Recursos de Terraform

| Recurso / archivo | Propósito |
|---|---|
| `google_compute_instance.source` + `source-startup.sh.tpl` | Origen listo para replicación lógica |
| `google_database_migration_service_connection_profile` x2 | Origen y destino (DMS crea Cloud SQL) |
| `google_database_migration_service_migration_job` | `CONTINUOUS` con `vpc_peering_connectivity` |
| `scripts/migrate.sh` | verify / start / status / promote / delete |
| Firewall `allow-dms-5432` | Solo desde rangos privados |

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `create_demo_source` | `true` | `false` + `source_host` para tu servidor real |
| `destination_tier` | db-custom-1-3840 |  |
| `source_subnet_cidr` | 10.90.0.0/24 |  |

Variables comunes (`common_variables.tf`): `project_id`, `region` (us-central1), `environment` (dev), `owner` (label), `cost_center`, `build_service_account`.

## Ejecución rápida

```bash
cd 03-cloud-e-infraestructura/lab11-terraform-gcp
gcloud auth login && gcloud auth application-default login
gcloud config set project <PROJECT_ID>
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/09-migration-dms/terraform.tfvars.example microlabs/09-migration-dms/terraform.tfvars   # edita los valores
bash scripts/lab.sh init  09-migration-dms
bash scripts/lab.sh apply 09-migration-dms
bash scripts/lab.sh test  09-migration-dms
bash scripts/lab.sh destroy 09-migration-dms
```

**Servidores completos (rehost de VMs):** el equivalente de AWS MGN en GCP es *Migrate to Virtual Machines* (fuentes VMware, AWS, Azure). Se opera desde la consola o con `gcloud migration vms`; el flujo es el mismo: fuente → replicación → *test clone* → *cut-over* → *finalize*.

## Prueba automatizada (`scripts/smoke-test.sh`)

El startup script del origen terminó; conteos `500,5000` en el origen (vía IAP SSH); estado del job y `verify`. Con `RUN_MIGRATION=1`: inicia el job y espera la fase **CDC**.

### Resultado esperado (extracto)

```
== Origen simulado (lab11-dev-dms-onprem-pg)
  OK   PostgreSQL listo con pglogical
  OK   Conteos en el origen (clientes,pedidos) (500,5000)
== Job de DMS (lab11-dev-dms-job)
  ..   Estado actual: NOT_STARTED
  OK   verify enviado
SMOKE TEST OK  (3 verificaciones)
```

## Parámetros en GitLab

| Variable | Tipo | Valor |
|---|---|---|
| `LAB09_TFVARS` | File | terraform.tfvars |

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `verify` falla: `pglogical not installed` | La extensión debe existir en **todas** las bases, incluida `postgres` (el script la crea). |
| Conexión rechazada desde DMS | El rango de PSA debe estar en `pg_hba.conf` (el script permite 10.0.0.0/8) y en el firewall. |
| Tablas sin replicar UPDATE/DELETE | DMS requiere PRIMARY KEY en cada tabla. |

## Google Cloud Architecture Framework (Well-Architected)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | verify antes de start; cutover explícito |
| Seguridad | Sin IPs públicas; Secret Manager; IAP |
| Confiabilidad | CDC continuo: RPO de segundos; el origen sigue vivo hasta promote |
| Rendimiento | Dump paralelo de DMS |
| Costos | DMS homogéneo sin costo; solo Cloud SQL y la VM |
| Sostenibilidad | Apagar el origen tras el cutover |

## Storage mínimo

| Recurso | Definición |
|---|---|
| VM origen | 20 GB |
| Cloud SQL destino | 20 GB SSD |

**Costo aproximado:** ~USD 2/día con la VM y Cloud SQL encendidos. **Destruye al terminar.**
