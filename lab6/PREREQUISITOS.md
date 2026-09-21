# Hoja de pre-requisitos — Lab 6 (SAP S/4HANA + Fiori)

Checklist para tener listo **antes** de empezar. Marca según la ruta que
elijas en [INSTALACION.md](INSTALACION.md): **A** = SAP CAL, **B** = BTP
Trial / desarrollo de apps, **C** = on-premise. Las cifras de hardware y
versiones son referencias generales: confirmarlas contra el sizing
(SAP Quick Sizer), el Product Availability Matrix (PAM) y las SAP Notes
de tu release.

## 1. Cuentas y accesos

| Requisito | A (CAL) | B (BTP Trial) | C (On-prem) |
|---|:-:|:-:|:-:|
| SAP Universal ID / S-user | Sí | Sí (Universal ID) | Sí (S-user con permisos de descarga) |
| Cuenta en <https://cal.sap.com> | Sí | No | No |
| Cuenta de nube propia (AWS / Azure / GCP) con método de pago | Sí | No | No |
| Cuenta SAP BTP Trial | No | Sí | No |
| Licencia de S/4HANA y acceso a SAP for Me / Maintenance Planner | No (viene en el appliance de prueba) | No | Sí |
| Permisos de administrador en tu equipo (hosts, instalaciones) | Sí | Sí | Sí |

## 2. Hardware e infraestructura

| Requisito | A (CAL) | B (BTP Trial) | C (On-prem) |
|---|---|---|---|
| RAM | La define la VM del appliance en tu nube | Tu equipo local: 8 GB mínimo, 16 GB recomendado | Mínimo ~128 GB para HANA + aplicación (según sizing) |
| Disco | Lo asigna el appliance | ~5 GB libres | Cientos de GB, separados en data / log / shared / backup |
| CPU | Según la VM elegida | 4 núcleos recomendado | Certificados para SAP HANA (Intel Xeon / IBM Power según PAM) |
| Red | Internet estable | Internet estable | IP fija, DNS/hostnames resolubles, puertos abiertos entre nodos |
| Presupuesto de nube | Sí: se paga la VM; apagarla cuando no se use | No | Servidor propio o IaaS certificado |

## 3. Sistema operativo y software base

**Ruta A y B (tu máquina)**
- Windows 10/11 (o macOS / Linux) con navegador Chrome o Edge actual.
- **SAP GUI for Windows** (solo si usarás transacciones; requiere descarga con S-user).
- **Node.js LTS** y **npm**.
- **VS Code** con la extensión **SAP Fiori tools** (o `@sap/generator-fiori` y `yo`).
- **Git**.
- Permiso para editar `C:\Windows\System32\drivers\etc\hosts`.

**Ruta C (servidor)**
- **SUSE Linux Enterprise Server for SAP Applications** o **Red Hat Enterprise Linux for SAP Solutions**, en una versión certificada según el PAM.
- Paquetes y parámetros de kernel que pidan las SAP Notes de HANA para tu SO.
- **SAP HANA** (instalador `hdblcm`), **SWPM** y el kernel, descargados del Software Download Center.
- **Maintenance Planner** para generar el `stack.xml`.

## 4. Red y seguridad

- Nombres de host y DNS fijos antes de instalar (cambiarlos después es costoso en on-prem).
- Puertos: HTTPS del ICM (por defecto `443xx`/`80xx`, según el número de instancia), `32NN` (SAP GUI), `3NN13`/`3NN15` (HANA). Confirmar en la documentación de tu release.
- Certificados TLS para el Fiori Launchpad (autofirmado sirve en laboratorio; en productivo uno de una CA).
- Ruta A: si usas VPN o túnel para llegar a la instancia, tenerlo instalado según la *Getting Started Guide*.

## 5. Conocimientos recomendados

- Conceptos de red (DNS, HTTPS, puertos) y administración básica de Linux (Ruta C).
- Lectura de la arquitectura: [ARQUITECTURA.md](ARQUITECTURA.md).
- Nociones de SAP Basis: mandantes, usuarios, roles (`PFCG`), transporte (`STMS`).
- Para desarrollo de apps: JavaScript, XML, OData y CDS/RAP a nivel introductorio.

## 6. Checklist final antes de empezar

- [ ] Elegí la ruta (A, B o C) y verifiqué que cumplo su columna de requisitos.
- [ ] Tengo S-user / Universal ID y, si aplica, cuenta CAL o BTP Trial activa.
- [ ] Tengo cuenta de nube con método de pago y límite de gasto configurado (Ruta A).
- [ ] Confirmé sizing y versiones contra PAM y SAP Notes (Ruta C).
- [ ] Instalé Node.js, VS Code y SAP Fiori tools (Rutas A/B para desarrollo).
- [ ] Puedo editar el archivo `hosts` y conozco el hostname/IP de mi instancia.
- [ ] Leí [ARQUITECTURA.md](ARQUITECTURA.md) e [INSTALACION.md](INSTALACION.md).
