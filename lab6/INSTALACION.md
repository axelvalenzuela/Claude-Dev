# Instalación de SAP S/4HANA + Fiori

> **Alcance honesto:** S/4HANA es software con licencia. No se descarga
> ni se instala con un `docker run` público, y un sistema on-prem
> completo pide **mínimo ~128 GB de RAM** (HANA in-memory) y cientos de
> GB de disco. Por eso este documento presenta las tres rutas reales y
> la recomendación para un laboratorio personal. Los números de versión
> cambian: confirmar siempre en SAP Note / Product Availability Matrix
> (PAM) antes de instalar.

## Elegir la ruta

| Ruta | Para qué | Costo/recursos | Esfuerzo |
|---|---|---|---|
| **A. SAP Cloud Appliance Library (CAL)** — "SAP S/4HANA Fully-Activated Appliance" | Aprender: sistema completo con Fiori ya activado y datos demo | Cuenta S-user/CAL + cuenta AWS/Azure/GCP propia; se paga la VM (se puede apagar) | Bajo (horas) |
| **B. SAP BTP Trial + ABAP Environment / Fiori tools** | Desarrollar apps Fiori/RAP sin infraestructura propia | Gratis (trial con límites) | Bajo |
| **C. On-premise real (SWPM + Maintenance Planner)** | Proyecto/cliente, entender la instalación de fondo | Licencia SAP, servidor 128 GB+ RAM, SLES/RHEL certificado | Alto (días/semanas) |

**Recomendación para este lab: A para ver el sistema completo, B para
construir apps.** C se documenta abajo a nivel conceptual.

---

## Ruta A — SAP CAL (recomendada)

1. Crear cuenta en <https://cal.sap.com> (requiere S-user o cuenta SAP
   Universal ID) y **vincular una cuenta de nube** (AWS/Azure/GCP).
2. En *Solutions* buscar **"SAP S/4HANA Fully-Activated Appliance"**
   (la versión más reciente disponible) → **Create Instance**.
3. Elegir región, tamaño de VM (el asistente sugiere el mínimo
   certificado) y **contraseña maestra**.
4. Esperar el aprovisionamiento (1–2 h la primera vez).
5. En la instancia: **Connect** → descargar la *Getting Started Guide*
   (trae IPs, usuarios y URLs) y agregar las entradas al archivo `hosts`
   (`C:\Windows\System32\drivers\etc\hosts`) o instalar el cliente
   VPN/tunel que indique.
6. **Apagar la VM cuando no la uses** (CAL cobra el cómputo de tu nube).

Accesos típicos (verificar en la guía de tu instancia):

| Qué | URL / dato |
|---|---|
| Fiori Launchpad | `https://<host>:<puerto>/sap/bc/ui2/flp?sap-client=100` |
| SAP GUI | Sistema `<host>`, instancia `00`, mandante `100` |
| Usuario dialog | El indicado en la Getting Started Guide |

## Ruta B — BTP Trial (desarrollo de apps)

1. Registrarse en <https://account.hanatrial.ondemand.com> (SAP BTP Trial).
2. Habilitar **SAP Build Work Zone** / **ABAP Environment** (trial)
   según disponibilidad.
3. Instalar en local: **Node.js LTS**, **VS Code**, y la extensión
   **SAP Fiori tools** (o `npm i -g @sap/generator-fiori yo`).
4. Generar app: `yo @sap/fiori` → elegir *SAP Fiori elements* →
   List Report Page, apuntando a un servicio OData V4.
5. Probar local: `npm start` (usa `fiori run`/`ui5 serve`).

## Ruta C — On-premise (resumen del procedimiento real)

1. **Prerrequisitos**: SLES for SAP o RHEL for SAP certificados; HANA
   sizing con *SAP Quick Sizer*; DNS/hostnames fijos; discos según
   sizing (data, log, shared, backup).
2. **Maintenance Planner** (SAP for Me): planificar el sistema →
   genera el *stack.xml* y las descargas.
3. **Descargas** del SAP Software Download Center: SWPM, kernel, HANA
   Database, componentes de S/4HANA.
4. **Instalar SAP HANA** con `hdblcm` (tenant DB + parámetros).
5. **Instalar S/4HANA con SWPM** (Software Provisioning Manager):
   ASCS + PAS + carga de base de datos. Se lanza con
   `./sapinst SAPINST_STACK_XML=<stack.xml>`.
6. **Licencia**: transacción `SLICENSE` (o hardware key + solicitud en
   el Marketplace).
7. **Post-instalación**: SPAM/SAINT, TMS (`STMS`), perfiles, backup.
8. **Activar Fiori** (sección siguiente).

---

## Activación de Fiori (modelo embedded)

Solo necesario en on-prem (Ruta C); la Ruta A ya viene activada.

1. **Servicios ICF (`SICF`)** — activar: `/sap/bc/ui2/flp`,
   `/sap/bc/ui5_ui5`, `/sap/opu/odata`, `/sap/public/bc/ui2`,
   `/sap/bc/ui2/start_up`.
2. **Rol de tarea**: ejecutar `STC01` con el task list
   `SAP_FIORI_LAUNCHPAD_INIT_SETUP` (activa servicios y parámetros
   base) y `SAP_GATEWAY_ACTIVATE_ALL` (Gateway).
3. **Servicios OData**: `/IWFND/MAINT_SERVICE` → *Add Service* →
   sistema `LOCAL` → elegir el servicio → asignar paquete/alias.
4. **Índice UI5**: ejecutar el reporte `/UI5/APP_INDEX_CALCULATE`.
5. **Roles (`PFCG`)**: crear rol, agregar el **catálogo** o **Space/Page**
   de las apps, asignar al usuario. Sin rol, el tile no aparece.
6. **Cache del FLP**: limpiar con `/UI2/INVALIDATE_CLIENT_CACHES`
   y `/UI2/INVALIDATE_GLOBAL_CACHES` tras cambios.

## Verificación

- `https://<host>:<puerto>/sap/bc/ui2/flp?sap-client=<mandante>` muestra el Launchpad.
- `.../sap/opu/odata/sap/<SERVICIO>_SRV/$metadata` responde XML (si pide login, es normal).
- SAP GUI: `SMICM` (ICM activo), `SICF` (servicio en verde), `/IWFND/ERROR_LOG` sin errores.

## Troubleshooting

| Síntoma | Causa típica | Dónde mirar |
|---|---|---|
| FLP en blanco / 404 | Servicio ICF inactivo | `SICF`, `SMICM` |
| Tile no aparece | Falta catálogo/space en el rol | `PFCG`, `/UI2/FLPD_CONF` |
| "No autorización" al abrir app | Objetos de autorización del OData | `SU53`, trace `ST01` |
| App no carga / error de librería UI5 | Índice desactualizado | `/UI5/APP_INDEX_CALCULATE` |
| OData 403/404 | Servicio sin activar en Gateway | `/IWFND/MAINT_SERVICE`, `/IWFND/ERROR_LOG` |
| Cambios no se reflejan | Cache del FLP | `/UI2/INVALIDATE_*` |
| HANA no arranca | RAM insuficiente / disco lleno | `HDB info`, logs en `/usr/sap/<SID>/HDB<NN>/<host>/trace` |
