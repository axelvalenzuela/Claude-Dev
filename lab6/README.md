# Laboratorio 6 — SAP S/4HANA + Fiori: instalación y arquitectura

Explica cómo se monta un ambiente S/4HANA con Fiori, cómo viaja una
petición por todas las capas, y aporta la automatización (Terraform,
Ansible y pipelines) para desplegarlo:

```
Browser → Fiori Launchpad → UI5 → OData/API → S/4HANA → ABAP → HANA
```

## Contenido

| Archivo | Qué contiene |
|---|---|
| [ARQUITECTURA.md](ARQUITECTURA.md) | Explicación capa por capa (diagrama, ejemplo de una petición completa, embedded vs. hub vs. cloud). |
| [PREREQUISITOS.md](PREREQUISITOS.md) | Requerimientos detallados: licencias, sizing, almacenamiento, datos, replicación/HA/DR, seguridad, backup, red y checklist. |
| [ASSESSMENT.md](ASSESSMENT.md) | Requisitos de inicio: qué entregar (licencias, secretos, medios), cuestionario de assessment y reglas de dimensionamiento. Alimenta a [tools/sizing.js](tools/sizing.js). |
| [terraform/](terraform/) | Plantilla Terraform modular (AWS): red, seguridad/KMS, nodos HANA con HA opcional, servidores ABAP y backup en S3. Validada con `terraform validate`; no aplicada. |
| [ansible/](ansible/) | Configuración automatizada sobre la infraestructura: SO, discos, HANA (hdblcm), System Replication, licencias y S/4HANA (SWPM). No ejecutada. |
| [pipelines/](pipelines/) | Pipelines (GitHub Actions en `.github/workflows/lab6-sap-pipeline.yml` y equivalente GitLab CI) que encadenan sizing → Terraform → Ansible con aprobación manual. |
| [INSTALACION.md](INSTALACION.md) | Tres rutas de instalación (SAP CAL, BTP Trial, on-prem con SWPM), activación de Fiori, verificación y troubleshooting. |

## Orden recomendado

1. [ARQUITECTURA.md](ARQUITECTURA.md): entender las capas.
2. [PREREQUISITOS.md](PREREQUISITOS.md): licencias, capacidad, datos, HA, seguridad.
3. [ASSESSMENT.md](ASSESSMENT.md): llenar el cuestionario y correr `node tools/sizing.js`.
4. [terraform/README.md](terraform/README.md) y [pipelines/README.md](pipelines/README.md): desplegar la infraestructura.
5. [INSTALACION.md](INSTALACION.md): activar Fiori y verificar.

## Estado de validación

| Pieza | Estado |
|---|---|
| `tools/sizing.js`, `tools/tf-to-inventory.js` | Probados localmente |
| Terraform (módulos del registry) | `terraform validate` pasa; sin `plan`/`apply` |
| Ansible, GitHub Actions, GitLab CI | Sintaxis YAML verificada; no ejecutados |
| Catálogo de instancias HANA | No verificado contra el directorio de plataformas certificadas de SAP |

## Nota importante

S/4HANA es software con licencia SAP y requiere infraestructura grande
(128 GB+ de RAM on-prem), así que **no se instaló en esta máquina**. Para
practicar, la ruta recomendada es SAP Cloud Appliance Library (sistema
completo con Fiori activado) y SAP BTP Trial para desarrollar apps.
Versiones, transacciones y URLs deben confirmarse contra tu release
concreto (SAP Notes / PAM).
