# 20 — Instrucciones

## Paso 1 — Beam local (gratis)

Beam va en su propio entorno virtual (es pesado y choca con otras librerías):

```bash
python -m venv .venv-beam
source .venv-beam/Scripts/activate         # Mac/Linux: .venv-beam/bin/activate
pip install -r 20_composer_dataflow/requirements-beam.txt pydantic
python 20_composer_dataflow/pipeline_ventas_beam.py
```

Salida esperada al final: `Reconciliación contra SAS: OK`. El resultado queda en `salida/beam_resumen_ventas.csv`.

## Paso 2 — El mismo pipeline en Dataflow (real, ~0.05 USD)

```bash
BUCKET=gs://$GCP_PROJECT_ID-migracion-sas
gcloud storage cp comun/datos/ventas.csv $BUCKET/datos/ventas.csv
python 20_composer_dataflow/pipeline_ventas_beam.py \
  --entrada $BUCKET/datos/ventas.csv --salida $BUCKET/resultados/beam_resumen.csv \
  --runner DataflowRunner --project $GCP_PROJECT_ID --region us-central1 \
  --temp_location $BUCKET/tmp \
  --service_account_email agente-migracion@$GCP_PROJECT_ID.iam.gserviceaccount.com
```

Míralo en **Dataflow > Trabajos** (tarda ~3–5 min: la mayor parte es levantar la máquina).
La cuenta de servicio necesita además `roles/dataflow.worker`:
`gcloud projects add-iam-policy-binding $GCP_PROJECT_ID --member=serviceAccount:agente-migracion@$GCP_PROJECT_ID.iam.gserviceaccount.com --role=roles/dataflow.worker`

## Paso 3 — El DAG de Composer

**Opción A (gratis, recomendada para estudiar):** lee el DAG y explica cada tarea. Compila con
`python -m py_compile 20_composer_dataflow/dag_migracion_sas.py`.

**Opción B (real, ~13 USD por día):**

```bash
gcloud composer environments create composer-lab8 --location us-central1 \
  --image-version composer-3-airflow-2 --environment-size small \
  --service-account agente-migracion@$GCP_PROJECT_ID.iam.gserviceaccount.com   # 20-30 min
gcloud composer environments storage dags import --environment composer-lab8 \
  --location us-central1 --source 20_composer_dataflow/dag_migracion_sas.py
```

En la UI de Airflow crea las *Variables* `proyecto_gcp`, `bucket_migracion`, `url_migrador`
(la URL de Cloud Run del lab 19) y da a la cuenta de servicio `roles/run.invoker`. Luego:

```bash
gcloud composer environments delete composer-lab8 --location us-central1   # ¡EL MISMO DÍA!
```

(El ID exacto de `--image-version` cambia con el tiempo: `gcloud composer environments create --help`
o la consola muestran los disponibles.)

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| `ImportError ... beam_interactive_api_pb2_grpc` en Windows | Ruta de más de 260 caracteres | Crea `.venv-beam` en una ruta corta o habilita *long paths* en Windows |
| Conflictos de versiones al instalar Beam | Mismo venv que el resto | Usa `.venv-beam` aparte |
| Dataflow: `The workers were unable to contact the service` / permisos | Falta `dataflow.worker` | Comando del paso 2 |
| Dataflow tarda mucho en arrancar | Levantar la VM | Normal para jobs pequeños; Dataflow brilla con volúmenes grandes |
| DAG no aparece en Airflow | Error de import | Airflow UI > *DAG import errors*; o `py_compile` local |
| Tarea `migrar_programa` con 403 | La cuenta de Composer no tiene `run.invoker` | Otorga el rol sobre el servicio de Cloud Run |
| Factura inesperada | Composer encendido | `gcloud composer environments list --locations us-central1` y borra |

## Retos

1. Agrega al pipeline una rama que escriba las ventas CANCELADAS en otro archivo (`beam.Partition`).
2. Agrega al DAG una tarea final que mande una alerta si algún programa quedó en `REQUIERE_REVISION`.
