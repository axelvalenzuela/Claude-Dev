# Micro lab 08: Amazon Neptune (grafos) con Serverless v2 y openCypher

> **Objetivo:** modelar relaciones (detección de fraude o recomendaciones) en una base de grafos totalmente privada, con autenticación IAM, carga masiva desde S3 y consultas openCypher desde Lambda.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~15 min · **Costo si queda encendido:** ~USD 115/mes ⚠️ destruir al terminar

**Prerrequisitos**

- Lab 00
- Presupuesto: ~USD 4/día

**1. Prepara las variables**

```bash
cd 03-cloud-e-infraestructura/lab10-terraform-aws
cp microlabs/08-data-neptune-graph/terraform.tfvars.example microlabs/08-data-neptune-graph/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `owner` | tu correo |
| `engine_version / neptune_family` | deben coincidir |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  08-data-neptune-graph
bash scripts/lab.sh plan  08-data-neptune-graph   # revisa qué se crea
bash scripts/lab.sh apply 08-data-neptune-graph
```

**3. Después del apply**

- El smoke test hace el bulk load de `data/*.csv`

**4. Verifica**

```bash
bash scripts/lab.sh test 08-data-neptune-graph   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 08-data-neptune-graph
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| data/nodes.csv, data/edges.csv | Tu modelo de grafo (formato openCypher) | Siempre |
| src/client/app.py | Acciones y consultas | Nuevos casos de uso |
| variables.tf → `min_ncu`, `max_ncu`, `instance_count` | Capacidad y HA | Carga real |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
                  VPC 10.80.0.0/16 (SIN NAT, sin Internet)
 ┌───────────────────────────────────────────────────────────────────┐
 │ subnets APP                         subnets DATA (aisladas)       │
 │ ┌──────────────┐  SigV4 :8182   ┌────────────────────────────┐    │
 │ │ Lambda client├───────────────►│ Neptune cluster            │    │
 │ │ SG client    │                │ db.serverless (1–4 NCU)    │    │
 │ └──────────────┘                │ IAM auth · KMS · audit log │    │
 │                                 └────────────┬───────────────┘    │
 │                                              │ /loader (rol rds)  │
 │                         S3 gateway endpoint ◄┘                    │
 └───────────────────────────────────────────────────────────────────┘
                                   ▼
                    S3 load bucket  sample/nodes.csv, edges.csv
```

## Modelo de datos (formato de carga openCypher)

- `data/nodes.csv`: `:ID,:LABEL,prop:Tipo`, con nodos Person, Account y Device.
- `data/edges.csv`: `:ID,:START_ID,:END_ID,:TYPE,prop:Tipo`, con relaciones FRIEND, OWNS, TRANSFER y USES.

## Pasos

```bash
terraform apply                       # ~10-15 min
FN=$(terraform output -raw client_function)
aws lambda invoke --function-name $FN --payload '{"action":"load"}' --cli-binary-format raw-in-base64-out out.json && cat out.json
aws lambda invoke --function-name $FN --payload '{"action":"load_status","load_id":"<loadId>"}' --cli-binary-format raw-in-base64-out out.json
```

Consultas de ejemplo (`{"action":"query","query":"..."}`):

```cypher
// Amigos de amigos (recomendación)
MATCH (a:Person {name:'Ana'})-[:FRIEND]->()-[:FRIEND]->(fof) RETURN DISTINCT fof.name
// Fraude: dispositivo compartido con una persona de alto riesgo
MATCH (p:Person)-[:USES]->(d:Device)<-[:USES]-(r:Person) WHERE r.risk > 80 AND p <> r RETURN p.name, d.name, r.name
// Transferencias cercanas al umbral de reporte
MATCH (src:Account)-[t:TRANSFER]->(dst:Account) WHERE t.amount > 9000 RETURN src.name, dst.name, t.amount
```

**Alternativa visual:** Neptune Workbench (notebook de SageMaker en la VPC) para explorar el grafo.

## Parámetros

| Variable | Default | Descripción |
|---|---|---|
| `engine_version` / `neptune_family` | `null` / `neptune1.4` | Deben ser compatibles entre sí |
| `min_ncu` / `max_ncu` | 1 / 4 | Escalado serverless (costo ∝ NCU-hora) |
| `instance_count` | 1 | 2 o más agregan réplicas multi-AZ (failover automático) |
| `backup_retention_days` | 7 | |
| `deletion_protection` | `false` | `true` en producción |

GitLab: `LAB08_TFVARS` (File).

<!-- detalle-funcional -->
## Ejecución rápida

```bash
cd 03-cloud-e-infraestructura/lab10-terraform-aws
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/08-data-neptune-graph/terraform.tfvars.example microlabs/08-data-neptune-graph/terraform.tfvars   # edita owner y demás
bash scripts/lab.sh init  08-data-neptune-graph
bash scripts/lab.sh apply 08-data-neptune-graph
bash scripts/lab.sh test  08-data-neptune-graph      # smoke test automatizado (abajo)
bash scripts/lab.sh destroy 08-data-neptune-graph
```

Con `make`: `make apply LAB=08-data-neptune-graph` · `make test LAB=08-data-neptune-graph`. Requisitos del smoke test: AWS CLI v2, `jq`, `curl` y credenciales con permisos de escritura sobre el lab.

## Prueba automatizada (`scripts/smoke-test.sh`)

Comprueba la conectividad (`RETURN 1` firmado con SigV4 desde la Lambda en la VPC), ejecuta el **bulk loader** si el grafo está vacío y espera `LOAD_COMPLETED`, valida 8 nodos y 9 relaciones, y corre 3 consultas de negocio (recomendación, fraude por dispositivo compartido y transferencias cercanas al umbral). Además verifica que el endpoint no es alcanzable desde Internet y que IAM auth está activo.

### Resultado esperado (extracto)

```
== Bulk load desde S3 (data/nodes.csv + data/edges.csv)
  ..   loadId: 7f9c...
  OK   LOAD_COMPLETED
  OK   Nodos (8)
  OK   Relaciones (9)
== Consultas de negocio
  OK   Recomendación: amigos de amigos de Ana (Carlos,)
  OK   Fraude: comparte dispositivo con persona de alto riesgo (Ana)
  OK   Transferencias cercanas al umbral de reporte (2)
SMOKE TEST OK  (10 verificaciones)
```

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `LOAD_FAILED` con `S3_ACCESS_DENIED` | Falta el S3 gateway endpoint en la route table de las subnets *data* o el rol del loader no puede `kms:Decrypt`. |
| La Lambda hace timeout | El SG del cliente no tiene egreso a 8182 hacia el SG de Neptune o la instancia todavía está `creating`. |
| `AccessDeniedException` en openCypher | La política usa `cluster_resource_id` (no el identificador); si recreaste el cluster vuelve a aplicar. |
| `InvalidParameterCombination` del parameter group | `neptune_family` no corresponde a la versión del motor; consulta `aws neptune describe-db-engine-versions --engine neptune`. |
<!-- detalle-funcional -->

## Well-Architected

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Audit logs en CloudWatch; carga reproducible desde Git → S3 |
| Seguridad | Sin Internet; IAM DB auth (SigV4); KMS; SG de cliente a cliente; rol de loader de solo lectura |
| Confiabilidad | Storage replicado 6 veces en 3 AZ; backups; réplicas opcionales |
| Eficiencia de rendimiento | Serverless v2 escala por NCU; timeout de query de 20 s |
| Optimización de costos | Sin NAT; NCU mínimo de 1; gateway endpoint gratuito |
| Sostenibilidad | Capacidad que sigue a la demanda |

## Storage mínimo

| Recurso | Definición |
|---|---|
| Neptune | Storage auto-escalable (10 GB → 128 TiB), sin preasignar; se cobra por GB-mes y por I/O |
| S3 | Archivos CSV de muestra (< 1 KB) |
| Backups | 7 días |

**Costo aproximado:** 1 NCU mínimo ≈ USD 0.16/h (~USD 115/mes si se deja encendido). **Destruye el lab al terminar.**
