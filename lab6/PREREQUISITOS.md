# Hoja de pre-requisitos — Lab 6 (SAP S/4HANA + Fiori)

Documento de requerimientos para levantar un ambiente S/4HANA con
Fiori. Cubre licenciamiento, capacidad, datos, replicación / alta
disponibilidad, seguridad, respaldo, operación y lo necesario para usar
la plantilla Terraform de [terraform/](terraform/).

Rutas de instalación (detalle en [INSTALACION.md](INSTALACION.md)):
**A** = SAP CAL, **B** = BTP Trial / desarrollo de apps,
**C** = on-premise o IaaS propio (la que automatiza Terraform).

> Las cifras (RAM, discos, puertos, tiempos) son **referencias
> generales**. Confirmarlas siempre contra SAP Quick Sizer, el Product
> Availability Matrix (PAM), el SAP Certified IaaS Platforms Directory y
> las SAP Notes de tu release. Donde se afirma algo sobre términos de
> licencia, la fuente válida es tu contrato con SAP.

## Índice

1. [Cuentas y accesos](#1-cuentas-y-accesos)
2. [Licenciamiento](#2-licenciamiento)
3. [Capacidad y sizing](#3-capacidad-y-sizing)
4. [Almacenamiento de HANA](#4-almacenamiento-de-hana)
5. [Datos](#5-datos)
6. [Replicación, alta disponibilidad y DR](#6-replicación-alta-disponibilidad-y-dr)
7. [Seguridad](#7-seguridad)
8. [Respaldo y recuperación](#8-respaldo-y-recuperación)
9. [Red](#9-red)
10. [Software base y herramientas](#10-software-base-y-herramientas)
11. [Operación y monitoreo](#11-operación-y-monitoreo)
12. [Pre-requisitos de Terraform / IaC](#12-pre-requisitos-de-terraform--iac)
13. [Checklist final](#13-checklist-final)

---

## 1. Cuentas y accesos

| Requisito | A (CAL) | B (BTP Trial) | C (On-prem / IaaS) |
|---|:-:|:-:|:-:|
| SAP Universal ID / S-user | Sí | Sí (Universal ID) | Sí, con autorización de descarga de software |
| Cuenta en <https://cal.sap.com> | Sí | No | No |
| Cuenta de nube propia (AWS / Azure / GCP) con método de pago | Sí | No | Sí (si es IaaS) |
| Cuenta SAP BTP Trial | No | Sí | No |
| Contrato/licencia S/4HANA + acceso a SAP for Me y Maintenance Planner | No | No | Sí |
| Administrador local (archivo `hosts`, instalaciones) | Sí | Sí | Sí |

## 2. Licenciamiento

El licenciamiento de SAP es contractual; lo siguiente ordena **qué
preguntar y validar** antes de instalar, no reemplaza tu contrato.

### 2.1 Licencias de SAP

| Elemento | Qué validar |
|---|---|
| **Producto** | Modalidad contratada: licencia on-premise (perpetua o suscripción) o **RISE with SAP** (S/4HANA Cloud, private edition, que ya incluye infraestructura). Esta guía asume on-premise / IaaS propio. |
| **Licencias por usuario** | Tipos de usuario de SAP (p. ej. Professional, Limited Professional, Employee, Developer, Self-Service) y cuántos de cada uno. Cada usuario de diálogo debe corresponder a un tipo contratado; el tipo se asigna en la transacción `SU01`. |
| **Licencias por métrica de volumen** | Algunos módulos se miden por volumen (documentos, ingresos, empleados, etc.), no por usuario. Confirmar métricas por solución. |
| **Base de datos HANA** | S/4HANA suele incluir una licencia de **HANA en modalidad de uso restringido (runtime)** para los datos de S/4HANA. Cargar datos ajenos a SAP o construir apps no-SAP encima puede requerir licencia *full-use*. Validar con tu ejecutivo de cuenta. |
| **Fiori** | El Fiori Launchpad y las apps estándar van incluidas con la licencia de S/4HANA; **SAP Build Work Zone** y otros servicios de BTP se licencian aparte. |
| **Clave de licencia del sistema** | Se solicita en el portal de SAP con el **hardware key** del sistema y se instala con la transacción `SLICENSE`. Tras instalar existe solo una licencia temporal de corta vigencia (verificar su duración para tu release); un sistema sin clave definitiva deja de operar al vencer. |
| **Soporte** | Nivel de soporte contratado (Enterprise Support, etc.): determina acceso a SAP Notes, parches y apertura de incidentes. |
| **Licencias no productivas** | Confirmar si dev/QAS están cubiertas por el contrato o requieren licencias adicionales. |

### 2.2 Licencias de terceros

| Elemento | Qué validar |
|---|---|
| Sistema operativo | **SLES for SAP Applications** o **RHEL for SAP Solutions** (necesarias para soporte SAP): suscripción propia (*BYOS*) o incluida en la hora de nube (*PAYG*). |
| Cliente/Servidor de respaldo | Herramienta con certificación **Backint** para HANA (si se usa una comercial). |
| Herramientas de seguridad | WAF, SIEM, antimalware certificado para SAP, si aplican. |
| Nube | Instancias certificadas para SAP HANA; descuentos por reserva (Savings Plans/Reserved) afectan el presupuesto. |

### 2.3 Rutas de prueba

- **SAP CAL / Trial**: licencias de evaluación **solo para no productivo y aprendizaje**; no usar para datos reales de negocio.

## 3. Capacidad y sizing

**Regla**: el tamaño lo define el **sizing**, no una estimación. Herramientas:

- **SAP Quick Sizer** (proyectos nuevos, por usuarios y volúmenes).
- **Reporte de sizing de HANA** (`/SDF/HDB_SIZING`, migraciones desde ECC/Suite on HANA).
- **SAP Notes de sizing** de tu release.

Datos que hay que tener para dimensionar:

| Entrada | Ejemplo |
|---|---|
| Usuarios concurrentes por tipo (dialog / Fiori / batch / API) | 50 dialog + 200 Fiori |
| Volumen de documentos por año y retención | 2 M partidas contables/año, 10 años |
| Tamaño actual de la base (migración) | 1.8 TB en ECC, 700 GB en HANA tras compresión |
| Picos y cierres (fin de mes, campañas) | Cierre contable día 1–5 |
| Integraciones e interfaces (IDocs, OData, API) | 30 interfaces, 5 masivas |
| Reporting analítico / embedded analytics | 20 usuarios pesados |

Referencia de orden de magnitud para el laboratorio (no productivo).
**Verificar contra el directorio de plataformas certificadas de SAP.**

| Entorno | HANA (RAM) | Aplicación ABAP | Uso |
|---|---|---|---|
| Sandbox / lab (recursos mínimos) | 128–256 GB | 32–64 GB, 8 vCPU | Aprendizaje, demos |
| Desarrollo / QAS | 256–512 GB | 64 GB, 8–16 vCPU | Desarrollo, pruebas |
| Productivo pequeño | 512 GB–1 TB | 2 × 64–128 GB | Según sizing real |

Capacidades adicionales a considerar:

- **vCPU**: la aplicación ABAP se dimensiona en **SAPS**; HANA depende de la
  arquitectura certificada, no solo del número de núcleos.
- **Ancho de banda de red** entre aplicación y HANA (baja latencia, mismo AZ / subred).
- **Crecimiento**: 3–5 años de proyección de datos.
- **Ambientes**: al menos DEV, QAS y PRD; para proyectos, sandbox y entrenamiento.

## 4. Almacenamiento de HANA

Guía de asignación (recomendaciones de SAP / proveedores de nube; validar
en el whitepaper *SAP HANA Storage Requirements* para tu versión):

| Volumen | Punto de montaje | Tamaño de referencia | Nota |
|---|---|---|---|
| Data | `/hana/data` | ≥ 1.2 × RAM | Ideal SSD/NVMe con alto rendimiento sostenido |
| Log | `/hana/log` | ≈ 0.5 × RAM (hasta 512 GB) | Latencia mínima de escritura crítica |
| Shared | `/hana/shared` | ≈ 1 × RAM (máx. 1 TB) | Binarios y trazas |
| Software SAP | `/usr/sap` | ~50 GB | Kernel, perfiles |
| Backup | `/backup` (o S3/Backint) | ≥ 2 × RAM | Puede vivir fuera de la VM |

- Cumplir los **KPIs de almacenamiento** de HANA (throughput y latencia)
  y validarlos con **HWCCT / HCMT** antes de cargar datos.
- Separar volúmenes por función (data, log, shared, backup).

## 5. Datos

| Tema | Qué definir |
|---|---|
| **Estrategia de carga** | *Greenfield* (nuevo, con migración de maestros y saldos), *Brownfield* (conversión del sistema ECC con SUM/DMO) o *Selective/Bluefield*. |
| **Origen y calidad** | Inventario de fuentes; limpieza de datos maestros (clientes, materiales, proveedores); deduplicación. |
| **Herramientas de migración** | SAP S/4HANA Migration Cockpit, SUM con DMO, SLT para replicación, LSMW (legado). |
| **Volumen y archivado** | Archivar datos antiguos antes de migrar reduce tamaño y costo de RAM. |
| **Datos de prueba** | En no productivo, usar datos **anonimizados/enmascarados**, no copias de producción sin tratar. |
| **Retención y legal** | Plazos de conservación (fiscal, laboral) y derecho de supresión (privacidad de datos personales aplicable). |
| **Cutover** | Plan de congelamiento, ventana de migración, conciliación de saldos y reversa. |
| **Gobierno** | Dueños de datos, catálogo, reglas de calidad y aprobaciones. |

## 6. Replicación, alta disponibilidad y DR

### 6.1 Conceptos de replicación de HANA (System Replication, HSR)

| Modo de sincronía | Cuándo confirma la escritura | RPO | Uso típico |
|---|---|---|---|
| `SYNC` | Log escrito en disco del secundario | Cero | HA en el mismo sitio / AZ cercana |
| `SYNCMEM` | Log en memoria del secundario | Casi cero | Equilibrio latencia/protección |
| `ASYNC` | No espera al secundario | Segundos–minutos | DR a otra región (distancia) |

Modos de operación: `delta_datashipping`, `logreplay` (recomendado; recuperación más rápida) y `logreplay_readenabled` (secundario legible).

### 6.2 Arquitecturas

| Nivel | Componentes | RTO/RPO orientativo |
|---|---|---|
| **Sin HA** (lab) | 1 nodo HANA + 1 aplicación | Restauración desde backup (horas) |
| **HA** | HANA primario + secundario (HSR, `SYNC/SYNCMEM`, otra AZ) + clúster **Pacemaker** con agentes `SAPHanaSR`; ASCS/ERS con **enqueue replication** | RTO minutos, RPO ≈ 0 |
| **HA + DR** | HA en una región + réplica `ASYNC` en otra región | RTO según runbook |

Requisitos de la capa de HA:

- Mecanismo de **fencing/STONITH** (en nube, vía API del proveedor) y **IP virtual / overlay IP** para la conmutación.
- **Al menos dos zonas de disponibilidad** con latencia baja.
- Almacenamiento independiente por nodo (HSR replica datos, no comparte disco).
- ASCS/ERS con sistema de archivos compartido (NFS/EFS) o clúster para `/sapmnt`.

### 6.3 Otras replicaciones

- **SLT / SDI** para replicar datos a analítica (no es HA).
- **Réplica de respaldos** a otra región/cuenta como protección contra desastres.

## 7. Seguridad

| Dominio | Requisito |
|---|---|
| **Identidad** | SSO (SAML 2.0 / Kerberos / OIDC) con el proveedor corporativo; MFA; ciclo de vida de usuarios; bloquear usuarios estándar (`SAP*`, `DDIC`) y `SYSTEM` de HANA para uso operativo. |
| **Autorizaciones** | Roles por `PFCG` con mínimo privilegio; segregación de funciones (SoD); revisión periódica; herramientas de GRC si el negocio lo exige. |
| **Red** | Segmentación (subredes privadas para HANA/app, acceso público solo al Web Dispatcher / balanceador); reglas de firewall por puerto; sin exposición directa de HANA. |
| **Cifrado en tránsito** | TLS en ICM/Web Dispatcher, SNC para SAP GUI, TLS entre app y HANA; certificados de una CA (autofirmado solo en laboratorio). |
| **Cifrado en reposo** | Volúmenes cifrados (KMS del proveedor) y cifrado nativo de HANA para data, log y backups. |
| **Secretos** | Contraseñas y claves en un gestor de secretos (Secrets Manager / Vault / SSM Parameter Store), nunca en el repositorio ni en `tfvars`. |
| **Auditoría** | *Audit log* de HANA, *Security Audit Log* (`SM19/SM20`) de ABAP, envío de logs a un SIEM. |
| **Parcheo** | Seguimiento de SAP Security Notes (día de parches mensual de SAP), parches del SO y del kernel. |
| **Hardening** | Guías de seguridad de SAP y CIS para SLES/RHEL; deshabilitar servicios ICF que no se usen (`SICF`). |
| **Fiori / web** | Cabeceras de seguridad (CSP, clickjacking), WAF frente al Web Dispatcher. |
| **Acceso administrativo** | Sin llaves SSH abiertas a Internet: usar SSM Session Manager o bastión con MFA. |
| **Cumplimiento** | Marcos aplicables (privacidad de datos personales, SOX, ISO 27001, PCI) y evidencias. |

## 8. Respaldo y recuperación

- **Backup de HANA**: completo + incremental/diferencial + **backup de log continuo**; con **Backint** (herramienta de respaldo certificada) o a archivo con copia externa.
- **Destino**: almacenamiento de objetos (p. ej. S3) con versionado, cifrado y bloqueo de acceso público.
- **Retención y RPO/RTO** acordados por escrito; **pruebas de restauración** periódicas (un backup no probado no cuenta).
- **Snapshots** de disco no reemplazan el backup consistente de HANA sin coordinación (usar la función de snapshot de HANA).
- **Aplicación ABAP**: respaldo de `/usr/sap`, `/sapmnt`, perfiles y transportes.

## 9. Red

- Nombres de host y DNS fijos **antes** de instalar (cambiarlos después es costoso).
- **Puertos** (NN = número de instancia; confirmar en la documentación de tu release):

| Servicio | Puerto |
|---|---|
| SAP GUI (dispatcher) | `32NN` |
| Message server (ASCS) | `36NN` / `39NN` |
| HTTP / HTTPS (ICM) | `80NN` / `443NN` |
| HANA SQL (SYSTEMDB / tenant) | `3NN13` / `3NN15` |
| HANA System Replication | `4NN01`–`4NN07` |
| SAP Start Service | `5NN13` / `5NN14` |

- Salida a Internet controlada (NAT) para repositorios, SAP Support y BTP.
- DNS interno, NTP sincronizado (crítico en clúster y certificados).
- Conectividad híbrida (VPN / Direct Connect) si se integra con el sistema corporativo.

## 10. Software base y herramientas

**Tu equipo (Rutas A y B)**
- Windows/macOS/Linux con Chrome o Edge.
- **SAP GUI** (si usarás transacciones).
- **Node.js LTS**, **npm**, **VS Code** + **SAP Fiori tools**, **Git**.

**Servidor (Ruta C)**
- **SLES for SAP** o **RHEL for SAP Solutions** en versión certificada (según PAM).
- Paquetes/parámetros de kernel indicados por las SAP Notes de HANA.
- **SAP HANA** (`hdblcm`), **SWPM**, kernel y componentes descargados del Software Download Center.
- **Maintenance Planner** para el `stack.xml`.

## 11. Operación y monitoreo

- Monitoreo de SO, HANA y aplicación (CloudWatch / Prometheus, SAP Cloud ALM o Solution Manager, HANA Cockpit).
- Alertas de disco, memoria, replicación, backups fallidos.
- Gestión de transportes (`STMS`), calendarios de parches, runbooks de incidentes.
- Cambios de infraestructura únicamente vía IaC y control de versiones.

## 12. Pre-requisitos de Terraform / IaC

Plantilla en [terraform/](terraform/) (AWS, modular). Requiere:

| Requisito | Detalle |
|---|---|
| Terraform | ≥ 1.5 (o OpenTofu compatible) |
| Proveedor | `hashicorp/aws` ~> 5.0 |
| Credenciales | Perfil/rol con permisos para VPC, EC2, EBS, KMS, IAM, S3 |
| Backend de estado | Bucket S3 + tabla DynamoDB de bloqueo (ver `backend.tf.example`) |
| AMI | SLES/RHEL for SAP de AWS Marketplace o suscripción BYOS (variable `ami_id`) |
| Cuotas de servicio | Cuota de vCPU para instancias con mucha memoria en la región |
| Presupuesto | Alarma de costos antes de `terraform apply` |

Para automatizar todo el flujo (assessment → sizing → pipeline → Ansible) ver [ASSESSMENT.md](ASSESSMENT.md) y [pipelines/README.md](pipelines/README.md).

Terraform crea la **infraestructura** (red, seguridad, cómputo, discos,
bucket de backup). La instalación de HANA/S/4HANA (`hdblcm`, SWPM) y el
clúster Pacemaker se hacen después sobre esa infraestructura.

## 13. Checklist final

**Cuentas y licencias**
- [ ] S-user / Universal ID y permisos de descarga.
- [ ] Contrato de S/4HANA, tipos y cantidades de usuarios, métrica de volumen definidos.
- [ ] Licencia de HANA (runtime vs. full-use) validada; plan para `SLICENSE`.
- [ ] Suscripción de SO (SLES/RHEL for SAP) definida (BYOS o PAYG).

**Capacidad y datos**
- [ ] Sizing ejecutado (Quick Sizer / `/SDF/HDB_SIZING`) y aprobado.
- [ ] Layout de discos de HANA definido y KPIs de almacenamiento validados.
- [ ] Estrategia de migración (greenfield / brownfield) y plan de calidad de datos.
- [ ] Datos de prueba anonimizados.

**Continuidad**
- [ ] Objetivos RPO/RTO acordados; arquitectura (sin HA / HA / HA+DR) elegida.
- [ ] Estrategia de backup con pruebas de restauración programadas.

**Seguridad**
- [ ] SSO/MFA, roles y SoD definidos; usuarios estándar bloqueados.
- [ ] Cifrado en tránsito y en reposo; gestor de secretos.
- [ ] Auditoría, parcheo y hardening planificados.

**Infraestructura**
- [ ] DNS, rangos de IP y puertos definidos.
- [ ] Cuenta de nube con presupuesto y cuotas de instancias.
- [ ] Terraform instalado, backend de estado creado y `ami_id` disponible.
- [ ] Leí [ARQUITECTURA.md](ARQUITECTURA.md), [INSTALACION.md](INSTALACION.md) y [terraform/README.md](terraform/README.md).
