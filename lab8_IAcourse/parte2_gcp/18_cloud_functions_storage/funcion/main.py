"""Cloud Function (2ª gen) disparada por eventos de Cloud Storage.

Flujo orientado a eventos: alguien sube un .sas al bucket -> la función se
despierta sola -> analiza el programa con el agente Analista -> deja el
resultado como JSON en el mismo bucket. Nadie tiene que "correr" nada.

    gs://BUCKET/entrada/ventas.sas   ──evento──>  analizar_sas()  ──>  gs://BUCKET/resultados/ventas.json

TRAMPA CLÁSICA: si la función escribe en el mismo bucket que la dispara y no
filtra por carpeta, su propio resultado vuelve a dispararla -> ciclo infinito
(y factura infinita). Por eso el filtro de `entrada/` y `.sas` va PRIMERO.
"""
import json
import sys
from pathlib import Path

# Desplegada: comun/ está junto a este archivo (lo copia desplegar.sh).
# En tu máquina: comun/ está en parte2_gcp/, dos carpetas arriba.
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parents[1]))

import functions_framework  # noqa: E402

from comun.agentes import analista  # noqa: E402
from comun.config import RAIZ, config  # noqa: E402

CARPETA_ENTRADA = "entrada/"
CARPETA_RESULTADOS = "resultados/"


def _log(severidad: str, mensaje: str, **campos):
    # Una línea JSON con "severity" -> Cloud Logging la muestra con nivel y campos.
    print(json.dumps({"severity": severidad, "message": mensaje, **campos}, ensure_ascii=False))


# --- Acceso a Storage (real o simulado en una carpeta local) ----------------
def _leer(bucket: str, nombre: str) -> str:
    if config.es_real:
        from google.cloud import storage

        return storage.Client().bucket(bucket).blob(nombre).download_as_text()
    return (RAIZ / "salida" / "gcs_simulado" / bucket / nombre).read_text(encoding="utf-8")


def _escribir(bucket: str, nombre: str, contenido: str) -> None:
    if config.es_real:
        from google.cloud import storage

        storage.Client().bucket(bucket).blob(nombre).upload_from_string(contenido, content_type="application/json")
        return
    ruta = RAIZ / "salida" / "gcs_simulado" / bucket / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")


# --- La función --------------------------------------------------------------
@functions_framework.cloud_event
def analizar_sas(cloud_event):
    datos = cloud_event.data
    bucket, nombre = datos["bucket"], datos["name"]

    # PASO 1: filtrar. Todo lo que no sea entrada/*.sas se ignora (evita el ciclo infinito).
    if not (nombre.startswith(CARPETA_ENTRADA) and nombre.endswith(".sas")):
        _log("INFO", "archivo ignorado", archivo=nombre)
        return

    # PASO 2: leer el programa SAS del bucket
    codigo = _leer(bucket, nombre)

    # PASO 3: analizar con el agente (mismo código que el lab 15)
    analisis, respuesta = analista(codigo)

    # PASO 4: guardar el resultado en resultados/
    destino = CARPETA_RESULTADOS + Path(nombre).stem + ".json"
    _escribir(bucket, destino, analisis.model_dump_json(indent=2))
    _log("INFO", "programa analizado", archivo=nombre, destino=destino, reglas=len(analisis.reglas),
         tokens=respuesta.tokens_entrada + respuesta.tokens_salida, costo_usd=respuesta.costo_usd)
