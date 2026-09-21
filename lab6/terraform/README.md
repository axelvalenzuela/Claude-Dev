# Terraform — infraestructura para SAP S/4HANA (AWS)

Plantilla modular que crea la **infraestructura** para un sistema
S/4HANA: red, seguridad, cifrado, nodos HANA (con o sin System
Replication), servidores de aplicación ABAP y bucket de backup. No
instala HANA ni S/4HANA (eso se hace con `hdblcm` y SWPM sobre estas
máquinas; ver [../INSTALACION.md](../INSTALACION.md)) ni configura el
clúster Pacemaker.

Requisitos y su justificación: [../PREREQUISITOS.md](../PREREQUISITOS.md).

> Estado: `terraform init -backend=false` y `terraform validate` pasan
> (Terraform 1.9.8, provider AWS 5.x). **No se ejecutó `plan` ni `apply`**
> contra una cuenta real. Los tipos de instancia y tamaños de disco de
> los `tfvars` son ejemplos: confirmarlos con el sizing y el directorio de
> plataformas certificadas de SAP antes de aplicar. Las instancias con
> mucha RAM son costosas.

## Estructura

```
terraform/
├── versions.tf            versión de Terraform y provider AWS
├── variables.tf           variables de entrada (con validaciones)
├── main.tf                composición de módulos
├── outputs.tf             IPs, bucket, KMS
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

## Qué decide cada módulo

| Módulo | Recursos | Decisiones de seguridad |
|---|---|---|
| `network` | VPC, subredes, IGW, NAT, rutas | Todo en subredes privadas; sin IP pública en instancias |
| `security` | KMS, SGs, IAM | Puertos derivados del número de instancia (`sap_instance_number`); HANA solo accesible desde la app y desde su par de replicación; acceso por SSM (sin SSH); `0.0.0.0/0` prohibido en `admin_cidrs` |
| `backup_storage` | S3 + política | Cifrado KMS, versionado, bloqueo de acceso público, denegación de tráfico sin TLS, paso a Glacier y expiración |
| `hana_nodes` | EC2, EBS gp3, attachments | Discos y raíz cifrados con KMS; IMDSv2 obligatorio; `secondary` solo si `ha_enabled = true`, en otra AZ |
| `app_server` | EC2, EBS | Mismos controles; servidores repartidos entre AZ |

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

## Después de Terraform (fuera del alcance de la plantilla)

1. Particionar y montar los discos (`/hana/data`, `/hana/log`, `/hana/shared`, `/backup`, `/usr/sap`) y validar KPIs con HCMT.
2. Instalar HANA (`hdblcm`) y S/4HANA (SWPM); cargar licencia (`SLICENSE`).
3. Con HA: configurar System Replication, Pacemaker/`SAPHanaSR`, fencing e IP virtual.
4. Configurar Backint/backups hacia el bucket, y activar Fiori (ver INSTALACION.md).

## Extender

- Otro proveedor de nube: reemplazar módulos manteniendo las mismas entradas (`nodes`, `volumes`).
- Web Dispatcher / balanceador: añadir un módulo `alb` que use `app_sg_id` y `private_subnet_ids`.
- Nuevo entorno: copiar `environments/dev.tfvars` a `qas.tfvars` y ajustar.
