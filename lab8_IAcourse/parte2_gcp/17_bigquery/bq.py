"""Ayudante de BigQuery para los scripts del lab 17.

MODO=real     -> google-cloud-bigquery contra tu proyecto (tablas creadas por infra/).
MODO=simulado -> SQLite local en salida/bigquery_simulado.db. SQLite entiende
                 el SQL sencillo de este lab (WITH, CASE, ROUND, GROUP BY, y
                 nombres entre `backticks`), así que puedes practicar gratis.
                 NO entiende funciones propias de BigQuery (QUALIFY, VECTOR_SEARCH...).
"""
from __future__ import annotations

import sqlite3

import pandas as pd

from comun.config import RAIZ, config

PRECIO_POR_TIB_USD = 6.25       # consultas on-demand; el primer 1 TiB de cada mes es gratis
MINIMO_FACTURADO_BYTES = 10 * 1024**2   # BigQuery cobra mínimo 10 MB por consulta


def tabla(nombre: str) -> str:
    """Nombre completo proyecto.dataset.tabla (en simulado, uno ficticio)."""
    proyecto = config.proyecto if config.es_real else "simulado"
    return f"{proyecto}.{config.dataset}.{nombre}"


def _cliente():
    config.exigir_proyecto()
    from google.cloud import bigquery

    return bigquery.Client(project=config.proyecto, location="US")


def _sqlite():
    ruta = RAIZ / "salida" / "bigquery_simulado.db"
    ruta.parent.mkdir(exist_ok=True)
    return sqlite3.connect(ruta)


def cargar_csv(ruta_csv, nombre_tabla: str) -> int:
    """Carga un CSV reemplazando el contenido de la tabla. Devuelve filas cargadas."""
    if not config.es_real:
        df = pd.read_csv(ruta_csv)
        with _sqlite() as con:
            df.to_sql(tabla(nombre_tabla), con, if_exists="replace", index=False)
        return len(df)

    from google.cloud import bigquery

    ajustes = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,   # recargar = idempotente
        autodetect=False,       # el esquema ya lo definió Terraform (infra/bigquery.tf)
    )
    with open(ruta_csv, "rb") as f:
        trabajo = _cliente().load_table_from_file(f, tabla(nombre_tabla), job_config=ajustes)
    trabajo.result()            # espera a que termine; lanza excepción si falló
    return trabajo.output_rows


def estimar(sql: str) -> dict:
    """DRY RUN: BigQuery valida el SQL y dice cuántos bytes leería, SIN ejecutarlo ni cobrar.
    Es la mejor forma de (1) validar SQL generado por un LLM y (2) evitar sorpresas de costo."""
    if not config.es_real:
        with _sqlite() as con:
            con.execute(f"EXPLAIN {sql}")        # valida sintaxis en SQLite
        return {"valido": True, "bytes": 0, "costo_usd": 0.0}

    from google.cloud import bigquery

    ajustes = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    trabajo = _cliente().query(sql, job_config=ajustes)
    facturables = max(trabajo.total_bytes_processed, MINIMO_FACTURADO_BYTES)
    return {"valido": True, "bytes": trabajo.total_bytes_processed,
            "costo_usd": facturables / 1024**4 * PRECIO_POR_TIB_USD}


def consultar(sql: str) -> pd.DataFrame:
    if not config.es_real:
        with _sqlite() as con:
            return pd.read_sql_query(sql, con)
    filas = _cliente().query(sql).result()
    # dict(fila) en vez de .to_dataframe(): evita instalar db-dtypes/pyarrow
    return pd.DataFrame([dict(f) for f in filas])
