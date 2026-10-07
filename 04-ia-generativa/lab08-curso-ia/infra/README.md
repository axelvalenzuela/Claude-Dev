# infra/ — Infraestructura como código (Terraform)

Crea todo lo que necesitan los labs 17–21 en tu proyecto de GCP, con permisos mínimos.

| Archivo | Crea |
|---|---|
| [apis.tf](apis.tf) | Habilita Vertex AI, BigQuery, Storage, Functions, Run, Eventarc, Build, Logging, Budgets, Dataflow |
| [storage.tf](storage.tf) | Bucket `PROYECTO-migracion-sas` (privado, borra archivos de más de 30 días) |
| [bigquery.tf](bigquery.tf) | Dataset `migracion_sas` + tablas `ventas`, `resumen_ventas`, `reporte_migracion`, `auditoria_llm` (particionada), `conocimiento` (vectores) |
| [iam.tf](iam.tf) | Cuenta de servicio `agente-migracion` con solo los roles necesarios + permiso de Storage→Eventarc |
| [presupuesto.tf](presupuesto.tf) | Presupuesto con alertas 50/90/100 % (opcional) |
| [outputs.tf](outputs.tf) | Nombres creados y siguientes pasos |

No crea Cloud Run ni la Cloud Function (se despliegan con `gcloud` en los labs 18–19,
para que veas el comando) ni Composer (caro; ver lab 20).

## Uso

```bash
cd 04-ia-generativa/lab08-curso-ia/infra
cp terraform.tfvars.example terraform.tfvars    # edita proyecto (y opcionalmente el presupuesto)
terraform init          # descarga el provider de Google (versión fijada en .terraform.lock.hcl)
terraform fmt           # formato estándar
terraform validate      # revisa sintaxis y referencias, sin tocar la nube
terraform plan          # muestra QUÉ va a crear/cambiar/borrar. Léelo siempre.
terraform apply         # lo crea (pide confirmación: escribe yes)
terraform output        # nombres para tu .env
terraform destroy       # borra todo al terminar
```

Costo de lo que crea este módulo sin uso: **~0 USD/mes** (bucket y dataset vacíos caben en
la capa gratuita; habilitar APIs y cuentas de servicio no cuesta). Ver [../docs/COSTOS_GCP.pdf](../docs/COSTOS_GCP.pdf).

## Buenas prácticas que se aplican aquí

- **Versiones fijadas**: `versions.tf` + `.terraform.lock.hcl` versionado → todos usan el mismo provider.
- **Estado fuera de git**: `terraform.tfstate` y `terraform.tfvars` están en `.gitignore`. En equipo, usa el backend `gcs` (comentado en `versions.tf`).
- **Mínimo privilegio**: roles a nivel dataset/bucket cuando se puede, no a nivel proyecto.
- **Etiquetas** (`labels`) en todo: permiten ver el costo del lab separado en la factura.
- **Nada público**: `public_access_prevention = "enforced"` en el bucket.
- **Lab ≠ producción**: `force_destroy`, `delete_contents_on_destroy` y `deletion_protection = false` facilitan borrar el lab; en producción van al revés.

## Si algo falla

| Error | Causa | Solución |
|---|---|---|
| `Error 403: ... has not been used in project ... or it is disabled` | La API aún se está activando | Espera 1–2 min y vuelve a `terraform apply` |
| `googleapi: Error 403: The caller does not have permission` | Tu usuario no es Owner/Editor | Pide el rol o usa un proyecto tuyo |
| `could not find default credentials` | Falta ADC | `gcloud auth application-default login` |
| Error en `google_billing_budget` sobre la moneda | `moneda_presupuesto` distinta a la de tu cuenta | Pon la moneda de tu cuenta (p. ej. `MXN`) |
| Error de permisos en `google_billing_budget` | No administras la cuenta de facturación | Deja `billing_account_id` vacío y crea el presupuesto en la consola |
| `Error 409: ... already exists` (bucket) | El nombre de bucket es global y ya existe | Cambia el nombre en `storage.tf` o importa el recurso |
| `Error acquiring the state lock` | Un apply anterior quedó a medias | `terraform force-unlock ID` (solo si seguro no hay otro apply corriendo) |
