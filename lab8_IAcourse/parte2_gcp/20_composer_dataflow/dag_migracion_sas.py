"""DAG de Airflow (Cloud Composer) que orquesta una migración por lotes.

Un DAG = tareas + dependencias + calendario + reintentos. Es lo que en SAS
harían los jobs calendarizados, pero con monitoreo, reintentos y alertas.

    listar_programas ──> migrar_programa (una tarea por programa, en paralelo) ──> cargar_reporte_a_bigquery

  listar_programas         lee gs://BUCKET/entrada/*.sas
  migrar_programa          llama POST /migrar de la API del lab 19 (Cloud Run)
  cargar_reporte_a_bigquery guarda estado/intentos/costo de cada programa en BigQuery

Para usarlo: copia este archivo a la carpeta dags/ del bucket de tu entorno
Composer (ver INSTRUCCIONES.md). Variables de Airflow necesarias:
    proyecto_gcp, bucket_migracion, url_migrador (la URL de Cloud Run)

NOTA: este archivo solo se ejecuta dentro de Airflow (no con `python`).
"""
from datetime import datetime, timedelta

try:                                   # Airflow 3 (Composer 3 con imágenes nuevas)
    from airflow.sdk import Variable, dag, task
except ImportError:                    # Airflow 2.x
    from airflow.decorators import dag, task
    from airflow.models import Variable


@dag(
    dag_id="migracion_sas_por_lotes",
    schedule="0 3 * * 1-5",            # 3 a.m. de lunes a viernes
    start_date=datetime(2026, 1, 1),
    catchup=False,                     # no "ponerse al día" con las fechas pasadas
    max_active_tasks=3,                # techo de llamadas simultáneas = techo de gasto en tokens
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["migracion", "ia"],
)
def migracion_sas_por_lotes():

    @task
    def listar_programas() -> list[str]:
        from google.cloud import storage

        bucket = Variable.get("bucket_migracion")
        blobs = storage.Client().list_blobs(bucket, prefix="entrada/")
        return [b.name for b in blobs if b.name.endswith(".sas")]

    @task
    def migrar_programa(nombre: str) -> dict:
        import google.auth.transport.requests
        import google.oauth2.id_token
        import requests
        from google.cloud import storage

        url = Variable.get("url_migrador")
        codigo = storage.Client().bucket(Variable.get("bucket_migracion")).blob(nombre).download_as_text()
        # Cloud Run está con --no-allow-unauthenticated: hay que mandar un ID token.
        token = google.oauth2.id_token.fetch_id_token(google.auth.transport.requests.Request(), url)
        r = requests.post(f"{url}/migrar", json={"programa": nombre.split("/")[-1], "codigo_sas": codigo},
                          headers={"Authorization": f"Bearer {token}"}, timeout=300)
        r.raise_for_status()
        datos = r.json()
        return {"programa": nombre, "estado": datos["estado"], "intentos": datos["intentos"],
                "costo_usd": datos["costo_usd"], "fecha": datetime.utcnow().isoformat()}

    @task
    def cargar_reporte_a_bigquery(resultados: list[dict]) -> None:
        from google.cloud import bigquery

        tabla = f"{Variable.get('proyecto_gcp')}.migracion_sas.reporte_migracion"
        errores = bigquery.Client().insert_rows_json(tabla, list(resultados))
        if errores:
            raise RuntimeError(f"Errores al insertar en BigQuery: {errores}")

    programas = listar_programas()
    resultados = migrar_programa.expand(nombre=programas)     # "dynamic task mapping": 1 tarea por programa
    cargar_reporte_a_bigquery(resultados)


migracion_sas_por_lotes()
