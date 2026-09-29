"""Prueba la Cloud Function en tu máquina, sin desplegar nada.

Construye a mano el mismo evento (CloudEvent) que Cloud Storage le mandaría
a la función al subir un archivo, y la llama directamente.

  PASO 1: "subir" ventas.sas a un bucket simulado (carpeta local)
  PASO 2: mandar el evento de entrada/ventas.sas     -> se analiza
  PASO 3: mandar el evento de resultados/ventas.json -> se IGNORA (sin ciclo infinito)

Correr (desde parte2_gcp/):   python 18_cloud_functions_storage/probar_local.py
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "funcion"))
from cloudevents.http import CloudEvent  # noqa: E402
from main import analizar_sas  # noqa: E402

from comun.config import RAIZ, config  # noqa: E402

BUCKET = "bucket-simulado"


def evento(nombre: str) -> CloudEvent:
    atributos = {
        "type": "google.cloud.storage.object.v1.finalized",
        "source": f"//storage.googleapis.com/projects/_/buckets/{BUCKET}",
    }
    return CloudEvent(atributos, {"bucket": BUCKET, "name": nombre})


def main():
    if config.es_real:
        sys.exit("Esta prueba local es para MODO=simulado. En real, sube el archivo con gcloud (ver INSTRUCCIONES.md).")

    # PASO 1
    destino = RAIZ / "salida" / "gcs_simulado" / BUCKET / "entrada" / "ventas.sas"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(RAIZ / "comun" / "sas" / "ventas.sas", destino)
    print(f"PASO 1: archivo en {destino.relative_to(RAIZ)}\n")

    # PASO 2
    print("PASO 2: evento entrada/ventas.sas")
    analizar_sas(evento("entrada/ventas.sas"))

    # PASO 3
    print("\nPASO 3: evento resultados/ventas.json (lo que la función acaba de escribir)")
    analizar_sas(evento("resultados/ventas.json"))

    resultado = RAIZ / "salida" / "gcs_simulado" / BUCKET / "resultados" / "ventas.json"
    print(f"\nResultado escrito en {resultado.relative_to(RAIZ)}:")
    print(resultado.read_text(encoding="utf-8")[:400], "...")


if __name__ == "__main__":
    main()
