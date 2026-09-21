# Terraform — infraestructura para SAP S/4HANA (AWS)

Plantilla modular que crea la **infraestructura** para un sistema
S/4HANA: red, seguridad, cifrado, nodos HANA (con o sin System
Replication), servidores de aplicación ABAP y bucket de backup. No
instala HANA ni S/4HANA (eso se hace con `hdblcm` y SWPM sobre estas
máquinas; ver [../INSTALACION.md](../INSTALACION.md)) ni configura el
clúster Pacemaker.

Requisitos y su justificación: [../PREREQUISITOS.md](../PREREQUISITOS.md).

> Estado: `terraform init -backend=false` y `terraform validate` pasan
> (Terraform 1.9.8, provider AWS 5.x y los módulos del registry). **No se ejecutó `plan` ni `apply`**
> contra una cuenta real. Los tipos de instancia y tamaños de disco de
> los `tfvars` son ejemplos: confirmarlos con el sizing y el directorio de
> plataformas certificadas de SAP antes de aplicar. Las instancias con
> mucha RAM son costosas.

Los valores de `environments/*.tfvars` pueden generarse a partir de un assessment con [../tools/sizing.js](../tools/sizing.js) (ver [../ASSESSMENT.md](../ASSESSMENT.md)), y el despliegue completo se automatiza con [../pipelines/](../pipelines/README.md).

## Estructura

```
terraform/
├── versions.tf            versión de Terraform y provider AWS
├── variables.tf           variables de entrada (con validaciones)
├── main.tf                composición de módulos
├── outputs.tf             IPs, IDs de instancias y volúmenes, bucket, KMS
├── backend.tf.example     estado remoto en S3 + DynamoDB
├── environments/
│   ├── dev.tfvars         un nodo HANA, sin HA
│   └── prd.tfvars         HANA primario + secundario, 2 servidores de aplicación
└── modules/
    ├── network/           VPC, subredes privadas (2 AZ), subred pública, NAT
    ├── security/          KMS, security groups (HANA/app), rol IAM + SSM
    ├── backup_storage/    S3 cifrado, versionado, lifecycle, solo TLS
    ├── hana_nodes/        EC2 HANA + volúmenes data/log/shared/backup
    └── app_server/        EC2 ABAP + volumen /usr/sap
```

## Módulos

La composición vive en `main.tf`. Cada módulo propio (`modules/*`) es una capa
fina de decisiones SAP (layout de discos HANA, puertos derivados del número de
instancia, reglas de seguridad) que **delega la creación de recursos en módulos
oficiales de [terraform-aws-modules](https://registry.terraform.io/namespaces/terraform-aws-modules)**
con la versión fijada (`~>`). No hay recursos `aws_*` sueltos, salvo un
`aws_iam_policy_document` (dato) y las consultas de AZ/AMI/cuenta.

| Módulo propio | Módulos del registry que usa | Decisiones SAP / de seguridad |
|---|---|---|
| `network` | `vpc` ~> 5.0 | Subredes privadas en 2 AZ, una pública solo para NAT, sin IP pública en instancias |
| `security` | `kms` ~> 3.0, `security-group` ~> 5.0 (x2), `iam/iam-policy` y `iam/iam-assumable-role` ~> 5.0 | Puertos derivados de `sap_instance_number`; HANA solo accesible desde la app y desde su par de replicación; acceso por SSM (sin SSH); `0.0.0.0/0` prohibido en `admin_cidrs` |
| `backup_storage` | `s3-bucket` ~> 4.0 | Cifrado KMS, versionado, bloqueo de acceso público, solo TLS, paso a Glacier y expiración |
| `hana_nodes` | `ec2-instance` ~> 5.0 | Discos data/log/shared/backup cifrados con KMS; IMDSv2 obligatorio; `secondary` solo si `ha_enabled = true`, en otra AZ |
| `app_server` | `ec2-instance` ~> 5.0 | Mismos controles; volumen `/usr/sap`; servidores repartidos entre AZ |

Los discos de datos se conservan al destruir las instancias
(`delete_volumes_on_termination = false`); `dev.tfvars` lo pone en `true`.
Al cambiar de versión de un módulo del registry, revisar su changelog y el `plan`.

## Uso

```bash
cd lab6/terraform

# (opcional) estado remoto
cp backend.tf.example backend.tf   # editar bucket/tabla

terraform init
terraform plan  -var-file=environments/dev.tfvars -var 'admin_cidrs=["203.0.113.10/32"]'
terraform apply -var-file=environments/dev.tfvars -var 'admin_cidrs=["203.0.113.10/32"]'
```

Antes del primer `apply`:

1. Suscribirte a la AMI de **SLES for SAP** (o RHEL for SAP) en AWS Marketplace,
   o pasar tu propia AMI con `-var ami_id=ami-xxxx`.
2. Verificar cuotas de vCPU para el tipo de instancia elegido.
3. Revisar `plan` línea por línea; no aplicar `prd.tfvars` sin sizing aprobado.

Acceso a las máquinas (sin SSH):

```bash
aws ssm start-session --target <instance-id>
```

Destruir el laboratorio: `terraform destroy -var-file=environments/dev.tfvars`
(el bucket de backup solo se borra con datos si `backup_force_destroy = true`,
que `dev.tfvars` activa y `prd.tfvars` no).

## Después de Terraform

Los pasos 1–3 los cubre la automatización de [../ansible/](../ansible/) (discos, HANA, System Replication, licencias); lo que falta es el clúster Pacemaker/fencing y Backint. Detalle en [../pipelines/README.md](../pipelines/README.md).

1. Particionar y montar los discos (`/hana/data`, `/hana/log`, `/hana/shared`, `/backup`, `/usr/sap`) y validar KPIs con HCMT.
2. Instalar HANA (`hdblcm`) y S/4HANA (SWPM); cargar licencia (`SLICENSE`).
3. Con HA: configurar System Replication, Pacemaker/`SAPHanaSR`, fencing e IP virtual.
4. Configurar Backint/backups hacia el bucket, y activar Fiori (ver INSTALACION.md).

## Extender

- Otro proveedor de nube: reemplazar módulos manteniendo las mismas entradas (`nodes`, `volumes`).
- Web Dispatcher / balanceador: añadir un módulo `alb` que use `app_sg_id` y `private_subnet_ids`.
- Nuevo entorno: copiar `environments/dev.tfvars` a `qas.tfvars` y ajustar.
