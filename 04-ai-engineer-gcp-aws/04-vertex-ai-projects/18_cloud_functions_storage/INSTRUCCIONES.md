# 18 — Instrucciones

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #23 de 26** · [← #22 BigQuery](../17_bigquery/README.md) · [#24 API en Cloud Run →](../19_cloud_run_api/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

## Paso #1 — Probar local (simulado)

```bash
python 18_cloud_functions_storage/probar_local.py
```

Observa: el evento de `entrada/ventas.sas` se procesa; el de `resultados/ventas.json` se ignora.
El "bucket" simulado es la carpeta `salida/gcs_simulado/`.

Opcional — servir la función como lo hace GCP (Functions Framework):

```bash
cd 18_cloud_functions_storage/funcion
functions-framework --target=analizar_sas --signature-type=cloudevent --port=8081
```

## Paso #2 — Desplegar (real)

Requisitos: `terraform apply` hecho (crea bucket, cuenta de servicio y el permiso Storage→Pub/Sub).

```bash
export GCP_PROJECT_ID=tu-proyecto
bash 18_cloud_functions_storage/desplegar.sh      # tarda 2-4 min la primera vez
```

## Paso #3 — Probar en la nube

```bash
gcloud storage cp comun/sas/ventas.sas gs://$GCP_PROJECT_ID-migracion-sas/entrada/ventas.sas
gcloud functions logs read analizar-sas --gen2 --region=us-central1 --limit=20
gcloud storage cat gs://$GCP_PROJECT_ID-migracion-sas/resultados/ventas.json
```

Los logs JSON también aparecen en **Logging > Explorador de registros** con el filtro
`resource.type="cloud_run_revision" jsonPayload.message="programa analizado"`.

## Paso #4 — Limpiar

```bash
gcloud functions delete analizar-sas --gen2 --region=us-central1
```

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| Deploy: `... service account ... does not have permission to publish to Pub/Sub` | Falta `pubsub.publisher` al agente de Storage | `terraform apply` (lo da `infra/iam.tf`) |
| Deploy: error de Cloud Build / permisos de build | La cuenta de build no tiene roles | `gcloud projects add-iam-policy-binding $GCP_PROJECT_ID --member=serviceAccount:NUMERO-compute@developer.gserviceaccount.com --role=roles/cloudbuild.builds.builder` |
| Deploy: `Validation failed for trigger` / región | Bucket y función en regiones incompatibles | Misma región (`us-central1`) para ambos |
| Subes el archivo y no pasa nada | El trigger tarda la 1.ª vez o falta `run.invoker`/`eventarc.eventReceiver` | Espera 2 min; `terraform apply`; revisa logs |
| La función se ejecuta sin parar | Escribe en la carpeta que la dispara | Nunca quites el filtro del PASO #1 |
| `ModuleNotFoundError: comun` desplegada | Desplegaste la carpeta `funcion/` directa | Usa `desplegar.sh` (copia `comun/`) |
| Timeout | Programa SAS enorme | Sube `--timeout`; para procesos largos usa Cloud Run Jobs |

## Retos

1. Haz que también ignore archivos de más de 200 KB (`datos["size"]`).
2. Cambia el destino para que además inserte una fila en BigQuery (`reporte_migracion`).
