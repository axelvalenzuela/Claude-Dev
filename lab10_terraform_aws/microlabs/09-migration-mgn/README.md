# Micro lab 09: Migraciones rehost con AWS Application Migration Service (MGN)

> **Objetivo:** preparar la *landing zone* de una migración lift-and-shift y recorrer el ciclo completo de MGN: replicación continua, prueba, cutover y finalización. Terraform crea la red, la seguridad, KMS y las identidades; la configuración de MGN se aplica con un script que usa los templates JSON renderizados por Terraform.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y lab 00).

**Tiempo de apply:** ~3 min + replicación · **Costo si queda encendido:** Según servidores

**Prerrequisitos**

- Lab 00
- Un servidor origen (VM en otra región/nube)

**1. Prepara las variables**

```bash
cd lab10_terraform_aws
cp microlabs/09-migration-mgn/terraform.tfvars.example microlabs/09-migration-mgn/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `owner` | tu correo |
| `source_cidrs` | IP pública del origen /32 |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>
bash scripts/lab.sh init  09-migration-mgn
bash scripts/lab.sh plan  09-migration-mgn   # revisa qué se crea
bash scripts/lab.sh apply 09-migration-mgn
```

**3. Después del apply**

- `bash microlabs/09-migration-mgn/scripts/configure-mgn.sh`
- Instala el agente en el origen (sección C)
- Test → Cutover → Finalize en la consola de MGN

**4. Verifica**

```bash
bash scripts/lab.sh test 09-migration-mgn   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 09-migration-mgn
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| templates/replication-template.json.tpl | Tipo de servidor, throttling, IP privada | Según enlace y volumen |
| templates/launch-template-overrides.json.tpl | Subnet, SG, perfil, etiquetas del destino | Por wave |
| variables.tf → `source_cidrs`, `target_app_ports` | Origen y puertos de la app | Siempre |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
 DATACENTER / OTRA NUBE                                   AWS (VPC 10.90.0.0/16)
 ┌──────────────────────┐   TCP 1500 (TLS)   ┌─────────────────────────────────────────┐
 │ Servidor origen      │───────────────────►│ Subnet STAGING                          │
 │  + AWS Replication   │   (Internet o      │  Replication servers t3.small (MGN)     │
 │    Agent             │    VPN/DX)         │  EBS staging gp3 cifrado con KMS        │
 └──────────┬───────────┘                    └───────────────┬─────────────────────────┘
            │ HTTPS 443 → mgn.<region>.amazonaws.com          │ conversión + launch
            ▼                                                 ▼
        Consola MGN ── Test ── Cutover ── Finalize   Subnets APP (privadas)
                                                      Instancias migradas: IMDSv2, SSM,
                                                      SG target, perfil IAM, EBS KMS
```

## Fases de la migración (las 7 R: este lab cubre *Rehost*)

| Fase | Acción | Herramienta |
|---|---|---|
| 1. Discover | Inventario y dependencias | Migration Hub / Application Discovery Service / Migration Evaluator |
| 2. Plan | Agrupar en **waves** y aplicaciones; definir runbook y ventana de cutover | MGN Applications & Waves |
| 3. Replicate | Instalar el agente; sincronización inicial y luego continua | MGN |
| 4. Test | Lanzar instancias de prueba y validar la app | MGN → *Launch test instances* |
| 5. Cutover | Congelar origen, sincronizar delta, lanzar y cambiar el DNS | MGN → *Launch cutover instances* |
| 6. Finalize | Detener la replicación y eliminar staging | MGN → *Finalize cutover* / *Archive* |
| 7. Optimize | Right-sizing, Savings Plans, replatform | Compute Optimizer |

## Pasos

### A. Infraestructura

```bash
cp terraform.tfvars.example terraform.tfvars   # source_cidrs = IP de tu VM origen
terraform apply
```

### B. Configurar MGN (requiere AWS CLI v2 y jq)

```bash
chmod +x scripts/configure-mgn.sh && ./scripts/configure-mgn.sh
```

### C. Instalar el agente en el servidor origen (Linux)

```bash
# 1) Credenciales temporales (requiere MFA)
aws sts assume-role --role-arn $(terraform output -raw agent_installer_role_arn) \
  --role-session-name mgn-install --serial-number <mfa-arn> --token-code <codigo>
# 2) En el servidor origen
wget -O ./aws-replication-installer-init https://aws-application-migration-service-us-east-1.s3.us-east-1.amazonaws.com/latest/linux/aws-replication-installer-init
chmod +x aws-replication-installer-init
sudo ./aws-replication-installer-init --region us-east-1 \
  --aws-access-key-id <AKIA..> --aws-secret-access-key <..> --aws-session-token <..> --no-prompt
```

En Windows se usa `AwsReplicationWindowsInstaller.exe` con los mismos parámetros.

> **Fuente de práctica:** si no tienes servidores on-premises, crea una VM en otra región o cuenta (o en VirtualBox con IP pública) e instala nginx para validar la app migrada.

### D. Re-ejecuta `configure-mgn.sh` (ya registra el nuevo source server) → Test → Cutover → Finalize.

## Templates

| Archivo | Uso |
|---|---|
| `templates/replication-template.json.tpl` | Subnet de staging, SG, cifrado CUSTOM KMS, ancho de banda, IP pública/privada |
| `templates/launch-template-overrides.json.tpl` | Subnet y SG destino, IMDSv2, perfil IAM, etiquetas |
| `scripts/configure-mgn.sh` | Inicializa MGN, actualiza el template de replicación y versiona los launch templates |

## Parámetros

| Variable | Default | Descripción |
|---|---|---|
| `source_cidrs` | (requerido) | IPs de origen permitidas en el puerto 1500 |
| `replication_over_private_link` | `false` | `true` con VPN/DX |
| `bandwidth_throttle_mbps` | 0 | Evita saturar el enlace del datacenter |
| `replication_server_instance_type` | t3.small | Usa uno mayor si hay muchos discos o mucho churn |
| `target_app_ports` | 80, 443 | |
| `installer_principal_arns` | `[]` | Quién puede instalar agentes |

### Parámetros en GitLab

| Variable | Tipo |
|---|---|
| `LAB09_TFVARS` | File |
| `MGN_SOURCE_CIDRS` | Variable → usar `TF_VAR_source_cidrs='["x.x.x.x/32"]'` |

## Seguridad y políticas

- Credenciales del agente **temporales**, con MFA obligatorio y la política administrada mínima `AWSApplicationMigrationAgentInstallationPolicy`.
- El puerto 1500 se abre solo a los CIDR de origen; los datos viajan cifrados con TLS y se cifran en reposo con la CMK.
- Los servidores migrados no tienen IP pública, usan IMDSv2 y se administran por SSM (se cierra SSH/RDP después del cutover).

<!-- detalle-funcional -->
## Ejecución rápida

```bash
cd lab10_terraform_aws
export TF_STATE_BUCKET=<output tf_state_bucket del lab 00>   # no aplica al lab 00
cp microlabs/09-migration-mgn/terraform.tfvars.example microlabs/09-migration-mgn/terraform.tfvars   # edita owner y demás
bash scripts/lab.sh init  09-migration-mgn
bash scripts/lab.sh apply 09-migration-mgn
bash scripts/lab.sh test  09-migration-mgn      # smoke test automatizado (abajo)
bash scripts/lab.sh destroy 09-migration-mgn
```

Con `make`: `make apply LAB=09-migration-mgn` · `make test LAB=09-migration-mgn`. Requisitos del smoke test: AWS CLI v2, `jq`, `curl` y credenciales con permisos de escritura sobre el lab.

## Prueba automatizada (`scripts/smoke-test.sh`)

Valida la landing zone (subnet de staging, SG de replicación solo en el puerto 1500 desde los CIDR de origen, SG destino sin SSH/RDP, rotación de la CMK y MFA en el rol instalador). Si MGN ya está inicializado, también valida el template de replicación (subnet de staging y cifrado CUSTOM) y lista los source servers con su estado de replicación, lag y fase del ciclo de vida.

### Práctica sin datacenter

1. Lanza una VM Ubuntu en **otra región** (simula el origen) con nginx y una página propia.
2. Pon su IP pública en `source_cidrs` y aplica; ejecuta `scripts/configure-mgn.sh`.
3. Instala el agente (ver sección C), espera `Healthy` + `Ready for testing` en la consola.
4. *Launch test instance* → valida con `curl` desde una instancia de la VPC → *Mark as ready for cutover* → *Launch cutover instance* → *Finalize cutover*.
5. Corre de nuevo el smoke test para ver el ciclo de vida actualizado.

### Resultado esperado (extracto)

```
== Red y seguridad
  OK   SG replicación: puerto 1500 de entrada (true)
  OK   SG replicación: sin 0.0.0.0/0 de entrada (0)
  OK   SG target: sin SSH/RDP abiertos (0)
== AWS MGN
  OK   Template usa la subnet de staging (subnet-0abc...)
  OK   Cifrado EBS CUSTOM (CUSTOM)
  ..   web-origen-01: CONTINUOUS · lag PT2S · ciclo READY_FOR_TEST
SMOKE TEST OK  (9 verificaciones)
```

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| El agente se queda en `Initial sync` sin avanzar | El origen no alcanza el replication server por TCP 1500 (firewall de salida del origen o `source_cidrs` incorrecto). |
| `Stalled` en la replicación | Los replication servers no salen por 443 hacia MGN/S3/EC2: sin IP pública necesitas NAT o VPC endpoints. |
| La instancia de prueba no arranca | Revisa el launch template: subnet y SG de `launch-template-overrides.json`; consulta el *Job log* en la consola de MGN. |
<!-- detalle-funcional -->

## Well-Architected (Migration Lens)

| Pilar | Implementación |
|---|---|
| Excelencia operativa | Waves, runbook, test antes del cutover, plantillas versionadas |
| Seguridad | KMS, MFA, credenciales temporales, SG mínimos, SSM |
| Confiabilidad | Replicación continua (RPO de segundos); rollback = mantener el origen hasta finalizar |
| Eficiencia de rendimiento | Right-sizing de MGN; throttling de ancho de banda |
| Optimización de costos | Replication servers compartidos; finalizar la replicación al terminar; Compute Optimizer después |
| Sostenibilidad | Consolidar y apagar el hardware on-premises |

## Storage mínimo

| Recurso | Definición |
|---|---|
| Staging | EBS gp3 ≈ tamaño de los discos origen (se cobra mientras se replica) + snapshots point-in-time |
| Target | EBS del mismo tamaño que el origen (ajustable en el launch template) |

**Costo:** MGN es gratis por 90 días por servidor; se pagan los replication servers, el EBS de staging y las instancias de prueba/cutover.
