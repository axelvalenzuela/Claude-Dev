# Micro lab 06: Arquitectura web de 3 niveles (ALB + Auto Scaling + RDS Multi-AZ)

> **Objetivo:** desplegar la arquitectura de referencia de 3 capas en una VPC multi-AZ. Cada capa vive en su propio módulo y en su propia subnet, y la seguridad se encadena por security groups.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y micro lab 00).

**Tiempo de apply:** ~15 min · **Costo si queda encendido:** ~USD 95/mes ⚠️ destruir al terminar

**Prerrequisitos**

- Micro lab 00
- Presupuesto: ~USD 3/día encendido

**1. Prepara las variables**

```bash
cd 08-terraform-aws
cp microlabs/06-web3tier-alb-asg-rds/terraform.tfvars.example microlabs/06-web3tier-alb-asg-rds/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `owner` | tu correo |
| `db_multi_az` | `false` para ahorrar en pruebas cortas |
| `certificate_arn` | opcional, ACM para HTTPS |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del micro lab 00>
bash scripts/lab.sh init  06-web3tier-alb-asg-rds
bash scripts/lab.sh plan  06-web3tier-alb-asg-rds   # revisa qué se crea
bash scripts/lab.sh apply 06-web3tier-alb-asg-rds
```

**3. Después del apply**

- Espera 3-5 min a que las instancias pasen el health check
- `curl $(terraform -chdir=microlabs/06-web3tier-alb-asg-rds output -raw app_url)/db`

**4. Verifica**

```bash
bash scripts/lab.sh test 06-web3tier-alb-asg-rds   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 06-web3tier-alb-asg-rds
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| modules/app-tier/user_data.sh.tpl | Tu aplicación real (o usar una AMI horneada) | Siempre en un proyecto real |
| modules/data-tier/main.tf | Motor, versión, clase, storage, parámetros | Por requisitos de la app |
| modules/web-tier/main.tf | Listeners, certificado, reglas WAF | Para HTTPS y rutas |
| main.tf → reglas `db_from_app` / `app_to_db` | Puertos entre capas | Si cambia el motor |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
                    Internet
                       │
              ┌────────▼─────────┐  subnets PUBLIC (AZ-a, AZ-b)
   Capa web   │ ALB + AWS WAF    │  SG alb: 80/443 desde 0.0.0.0/0
              └────────┬─────────┘
                       │ solo SG alb → SG app :80
              ┌────────▼─────────┐  subnets APP (privadas, salida vía NAT)
   Capa app   │ ASG t4g (2..4)   │  IMDSv2, sin SSH, SSM Session Manager
              │ target tracking  │  rol IAM: SSM + CW + leer 1 secreto
              └────────┬─────────┘
                       │ solo SG app → SG db :5432
              ┌────────▼─────────┐  subnets DATA (aisladas, SIN ruta a Internet)
   Capa datos │ RDS PostgreSQL   │  Multi-AZ, gp3 20→100 GB, KMS, TLS forzado,
              │ primary │ standby│  password en Secrets Manager, backups 7 días
              └──────────────────┘
```

## Estructura modular

```
06-web3tier-alb-asg-rds/
├── main.tf               # composición + reglas entre capas + alarmas
└── modules/
    ├── web-tier/         # ALB, listeners, target group, WAF
    ├── app-tier/         # launch template, ASG, scaling, IAM, user_data.sh.tpl
    └── data-tier/        # RDS, subnet group, parameter group, SG
```

> Las reglas `db_from_app` / `app_to_db` se definen en el root para romper la dependencia circular (app necesita el endpoint de la BD y la BD necesita el SG de app).

## Pasos

```bash
terraform apply           # ~15 min (RDS Multi-AZ)
curl $(terraform output -raw app_url)       # repite: verás instancias de distintas AZ
aws ssm start-session --target <instance-id>  # acceso sin SSH
```

**Pruebas de resiliencia:**
- Termina una instancia: el ASG la reemplaza y el ALB deja de enviarle tráfico.
- `aws rds reboot-db-instance --db-instance-identifier aie-dev-3t-db --force-failover`: failover a la otra AZ en 1 a 2 minutos.
- Carga de CPU: `stress-ng` vía SSM para disparar el scale-out.

## Parámetros

| Variable | Default | Nota |
|---|---|---|
| `vpc_cidr` | `10.60.0.0/16` | /24 por subnet (public 0-2, app 10-12, data 20-22) |
| `single_nat_gateway` | `true` | `false` en producción |
| `certificate_arn` | `null` | ACM para HTTPS + redirect |
| `app_instance_type` / `app_min_size` / `app_max_size` | t4g.micro / 2 / 4 | |
| `db_instance_class` | db.t4g.micro | |
| `db_allocated_storage_gb` | 20 | Mínimo de gp3; autoscaling hasta 100 GB |
| `db_multi_az` | `true` | |
| `deletion_protection` | `false` | `true` en producción (ALB + RDS + snapshot final) |

GitLab: `AWS06_TFVARS` (File). Como RDS tarda en crearse, deja el job de apply con `timeout: 1h`.

<!-- detalle-funcional -->
## Ejecución rápida

```bash
cd 08-terraform-aws
export TF_STATE_BUCKET=<output tf_state_bucket del micro lab 00>   # no aplica al micro lab 00
cp microlabs/06-web3tier-alb-asg-rds/terraform.tfvars.example microlabs/06-web3tier-alb-asg-rds/terraform.tfvars   # edita owner y demás
bash scripts/lab.sh init  06-web3tier-alb-asg-rds
bash scripts/lab.sh apply 06-web3tier-alb-asg-rds
bash scripts/lab.sh test  06-web3tier-alb-asg-rds      # smoke test automatizado (abajo)
bash scripts/lab.sh destroy 06-web3tier-alb-asg-rds
```

Con `make`: `make apply LAB=06-web3tier-alb-asg-rds` · `make test LAB=06-web3tier-alb-asg-rds`. Requisitos del smoke test: AWS CLI v2, `jq`, `curl` y credenciales con permisos de escritura sobre el lab.

## Prueba automatizada (`scripts/smoke-test.sh`)

Espera a que el ALB responda, verifica 2 targets sanos y balanceo entre **2 AZ**, y llama a `/db`: la app lee la contraseña de **Secrets Manager**, crea la tabla `visits`, inserta una fila y confirma que la conexión usa **TLS**. También comprueba que RDS no es público, que es Multi-AZ, que IMDSv2 es obligatorio y que el WAF bloquea una inyección SQL.

`CHAOS=1 bash scripts/lab.sh test 06-web3tier-alb-asg-rds` termina una instancia y mide cuántos requests fallan mientras el ASG se recupera.

### La aplicación

`modules/app-tier/user_data.sh.tpl` instala un servicio `systemd` (`aie-app`) en Python con solo librería estándar:

| Ruta | Qué hace |
|---|---|
| `/` | HTML con la instancia y la AZ que respondió |
| `/health` | Health check del target group |
| `/db` | Lee el secreto, ejecuta SQL contra RDS por TLS y devuelve un JSON con visitas, versión de PostgreSQL y uso de SSL |

Para conectarte a una instancia (sin SSH): `aws ssm start-session --target <instance-id>` y luego `journalctl -u aie-app -f`.

### Resultado esperado (extracto)

```
== Capa web: ALB (http://aie-dev-3t-123.us-east-1.elb.amazonaws.com)
  OK   ALB responde 200 en /health
  OK   Targets sanos (2)
== Capa app: balanceo multi-AZ
  OK   Respuestas desde 2 AZ distintas (us-east-1a us-east-1b)
== Capa datos: RDS PostgreSQL vía Secrets Manager
  OK   Estado /db (ok)
  OK   Conexión cifrada TLS (rds.force_ssl) (true)
== WAF
  OK   Ataque SQLi bloqueado (403)
SMOKE TEST OK  (11 verificaciones)
```

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| Targets `unhealthy` por varios minutos | El user_data todavía instala paquetes (2-3 min). Revisa `/var/log/cloud-init-output.log` vía SSM. Sin NAT las instancias no pueden descargar paquetes. |
| `/db` devuelve 500 `timeout expired` | Falta la regla `db_from_app` o el SG de la app no tiene egreso a 5432; revisa con *VPC Reachability Analyzer*. |
| `/db` devuelve 500 `AccessDeniedException` de Secrets Manager | El rol de la instancia solo puede leer el secreto de RDS; si recreaste la BD cambió el ARN; aplica de nuevo para actualizar la política. |
| `destroy` tarda o falla en RDS | Con `deletion_protection = true` primero desactívala; el snapshot final se conserva. |
<!-- detalle-funcional -->

## Well-Architected

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Módulos por capa; instance refresh rolling; logs de PostgreSQL en CloudWatch |
| Seguridad | WAF (Common + SQLi + rate), SG encadenados, subnets de datos aisladas, IMDSv2, sin SSH, Secrets Manager, KMS, TLS forzado, IAM DB auth |
| Confiabilidad | Multi-AZ en todas las capas; health checks del ELB; backups de 7 días; storage autoscaling |
| Eficiencia de rendimiento | Graviton (t4g); target tracking; Performance Insights |
| Optimización de costos | NAT único en dev; tamaños mínimos; ASG elástico |
| Sostenibilidad | Graviton (menor energía por cómputo); escalar a la demanda |

## Storage mínimo

| Recurso | Definición |
|---|---|
| EBS raíz app | 8 GB gp3 cifrado por instancia |
| RDS | 20 GB gp3 (mínimo), autoscaling a 100 GB, backups 7 días |
| Logs | Flow logs (REJECT) 14 días |

**Costo aproximado (us-east-1, 24/7):** NAT ~USD 33, ALB ~USD 18, 2× t4g.micro ~USD 12, RDS t4g.micro Multi-AZ ~USD 25, WAF ~USD 8. **Destruye el lab al terminar.**

## Limpieza

`terraform destroy`
