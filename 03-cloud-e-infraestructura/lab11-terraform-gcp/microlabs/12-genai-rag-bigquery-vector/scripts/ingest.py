"""Ingesta de la base de conocimiento: documentos -> chunks -> embeddings en BigQuery.

    python scripts/ingest.py                    # usa data/*.md
    python scripts/ingest.py --docs mis_docs/   # tus propios .md o .txt

Conceptos que muestra:
  - Chunking por párrafos con tamaño máximo y solapamiento (overlap) para no cortar ideas.
  - Re-ingesta idempotente: borra los chunks del mismo archivo antes de insertar.
  - Los embeddings se generan DENTRO de BigQuery (ML.GENERATE_EMBEDDING), sin código de ML.
"""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

from google.cloud import bigquery

LAB = Path(__file__).resolve().parent.parent


def tf_output(name):
    return subprocess.run(["terraform", f"-chdir={LAB}", "output", "-raw", name],
                          check=True, capture_output=True, text=True).stdout.strip()


def chunk(text, max_chars=900, overlap_chars=150):
    """Agrupa párrafos hasta max_chars; cada chunk repite el final del anterior (overlap)."""
    chunks, current = [], ""
    for paragraph in [p.strip() for p in text.split("\n\n") if p.strip()]:
        if current and len(current) + len(paragraph) > max_chars:
            chunks.append(current)
            current = current[-overlap_chars:] + "\n"
        current += paragraph + "\n"
    if current.strip():
        chunks.append(current)
    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", default=str(LAB / "data"))
    parser.add_argument("--max-chars", type=int, default=900)
    args = parser.parse_args()

    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or tf_output("chunks_table").split(".")[0]
    dataset = tf_output("dataset")
    client = bigquery.Client(project=project)

    rows = []
    for path in sorted(Path(args.docs).glob("*.[mt][dx]*")):
        for i, text in enumerate(chunk(path.read_text(encoding="utf-8"), args.max_chars)):
            chunk_id = hashlib.sha1(f"{path.name}:{i}:{text}".encode()).hexdigest()[:16]
            rows.append({"chunk_id": chunk_id, "source": path.name, "content": text})
    print(f"{len(rows)} chunks de {len({r['source'] for r in rows})} documentos")

    staging = f"{project}.{dataset}.chunks_staging"
    client.load_table_from_json(rows, staging, job_config=bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        schema=[bigquery.SchemaField(n, "STRING") for n in ("chunk_id", "source", "content")],
    )).result()

    sql = f"""
    DELETE FROM `{project}.{dataset}.chunks` WHERE source IN (SELECT DISTINCT source FROM `{staging}`);
    INSERT INTO `{project}.{dataset}.chunks` (chunk_id, source, content, embedding, ingested_at)
    SELECT chunk_id, source, content, ml_generate_embedding_result, CURRENT_TIMESTAMP()
    FROM ML.GENERATE_EMBEDDING(
      MODEL `{project}.{dataset}.embedding_model`,
      (SELECT chunk_id, source, content FROM `{staging}`),
      STRUCT('RETRIEVAL_DOCUMENT' AS task_type, TRUE AS flatten_json_output))
    WHERE ml_generate_embedding_status = '';
    """
    client.query(sql).result()

    stats = list(client.query(f"SELECT COUNT(*) AS n, COUNT(DISTINCT source) AS docs FROM `{project}.{dataset}.chunks`").result())[0]
    print(json.dumps({"chunks_en_tabla": stats.n, "documentos": stats.docs}))


if __name__ == "__main__":
    main()
