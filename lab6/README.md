# Laboratorio 6 — SAP S/4HANA + Fiori: instalación y arquitectura

Lab de documentación (sin código de aplicación). Explica cómo se monta
un ambiente S/4HANA con Fiori y cómo viaja una petición por todas las
capas:

```
Browser → Fiori Launchpad → UI5 → OData/API → S/4HANA → ABAP → HANA
```

## Contenido

| Archivo | Qué contiene |
|---|---|
| [ARQUITECTURA.md](ARQUITECTURA.md) | Explicación capa por capa (diagrama, ejemplo de una petición completa, embedded vs. hub vs. cloud). |
| [PREREQUISITOS.md](PREREQUISITOS.md) | Hoja de pre-requisitos por ruta: cuentas, hardware, software, red y checklist previo. |
| [INSTALACION.md](INSTALACION.md) | Tres rutas de instalación (SAP CAL, BTP Trial, on-prem con SWPM), activación de Fiori, verificación y troubleshooting. |

## Nota importante

S/4HANA es software con licencia SAP y requiere infraestructura grande
(128 GB+ de RAM on-prem), así que **no se instaló en esta máquina**. Para
practicar, la ruta recomendada es SAP Cloud Appliance Library (sistema
completo con Fiori activado) y SAP BTP Trial para desarrollar apps.
Versiones, transacciones y URLs deben confirmarse contra tu release
concreto (SAP Notes / PAM).
