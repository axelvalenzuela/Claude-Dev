"""11 · BigQuery desde Python: estimar el costo con dry run y luego consultar (integra el micro lab GCP 08).

Concepto: BigQuery cobra por bytes escaneados. Un dry run dice cuánto costará SIN ejecutar.
Filtrar por la columna de partición y por las de clustering reduce los bytes drásticamente.

    export RAW_TABLE=$(terraform -chdir=../microlabs/08-data-bigquery-analytics output -raw raw_table)
    python 11_bigquery_consulta.py
"""

import os

from google.cloud import bigquery

client = bigquery.Client(project=os.environ["GOOGLE_CLOUD_PROJECT"])
table = os.environ["RAW_TABLE"]

sql = f"""
SELECT event_type, COUNT(*) AS eventos, SUM(IFNULL(amount, 0)) AS ingresos
FROM `{table}`
WHERE DATE(event_ts) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)   -- filtro de partición (obligatorio)
  AND country = 'MX'                                               -- aprovecha el clustering
GROUP BY event_type ORDER BY eventos DESC
"""

dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
print(f"Dry run: escanearía {dry.total_bytes_processed / 1e6:.2f} MB (USD ~{dry.total_bytes_processed / 1e12 * 6.25:.6f})")

for row in client.query(sql).result():
    print(f"{row.event_type:12} eventos={row.eventos:4} ingresos={row.ingresos}")
