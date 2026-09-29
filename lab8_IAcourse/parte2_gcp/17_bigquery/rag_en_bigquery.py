"""Micro lab 17 (extra) — BigQuery como base de datos vectorial (solo MODO=real).

En el lab 13 el índice vive en un archivo JSON. En producción necesitas que
viva en un servicio. Opciones en GCP, de más simple a más especializada:
    BigQuery + VECTOR_SEARCH   <- este script: sin servidores extra, pagas por consulta
    AlloyDB / Cloud SQL + pgvector
    Vertex AI Vector Search    (baja latencia a gran escala, pero cobra por nodo encendido)

  PASO 1: reutilizar los fragmentos + embeddings del lab 13
  PASO 2: cargarlos a la tabla `conocimiento` (columna embedding ARRAY<FLOAT64>)
  PASO 3: embeber la pregunta y buscar con VECTOR_SEARCH (distancia coseno)

Correr (desde parte2_gcp/, con MODO=real y después de terraform apply):
    python 17_bigquery/rag_en_bigquery.py "¿cómo quito registros repetidos?"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "13_embeddings_rag"))
import bq  # noqa: E402

from comun import llm  # noqa: E402
from comun.config import config  # noqa: E402

CONSULTA = """
SELECT base.fuente, base.texto, distance
FROM VECTOR_SEARCH(
  TABLE `{tabla}`, 'embedding',
  (SELECT @pregunta AS embedding),
  top_k => 3,
  distance_type => 'COSINE'
)
ORDER BY distance
"""


def main():
    if not config.es_real:
        print("Este script usa VECTOR_SEARCH de BigQuery: requiere MODO=real (ver docs/CONECTAR_GCP.md).")
        print("Mientras tanto, lee la consulta que ejecutaría:\n" + CONSULTA.format(tabla=bq.tabla("conocimiento")))
        return

    from google.cloud import bigquery
    from rag_sas import construir_indice   # lab 13

    cliente = bq._cliente()
    # PASO 1 y 2 — cargar fragmentos con su vector (WRITE_TRUNCATE = se puede repetir sin duplicar)
    filas = [{"fuente": f["fuente"], "texto": f["texto"], "embedding": f["vector"]} for f in construir_indice()]
    trabajo = cliente.load_table_from_json(
        filas, bq.tabla("conocimiento"),
        job_config=bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE),
    )
    trabajo.result()
    print(f"{len(filas)} fragmentos cargados en {bq.tabla('conocimiento')}")

    # PASO 3 — buscar
    pregunta = " ".join(sys.argv[1:]) or "¿Cómo quito registros repetidos de una tabla?"
    vector = llm.embeber([pregunta], tipo="RETRIEVAL_QUERY")[0]
    ajustes = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ArrayQueryParameter("pregunta", "FLOAT64", vector)]
    )
    print(f"\nPREGUNTA: {pregunta}")
    for fila in cliente.query(CONSULTA.format(tabla=bq.tabla("conocimiento")), job_config=ajustes).result():
        print(f"  distancia {fila['distance']:.3f}  [{fila['fuente']}] {fila['texto'][:80]}...")


if __name__ == "__main__":
    main()
