"""RAG sobre BigQuery: embedding de la pregunta + VECTOR_SEARCH + Gemini con citas."""

import json
import logging
import os

import functions_framework
from google import genai
from google.cloud import bigquery
from google.genai import types

logging.basicConfig(level=logging.INFO, format="%(message)s")

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
DATASET = os.environ["DATASET"]
TOP_K = int(os.environ.get("TOP_K", "4"))
MAX_DISTANCE = float(os.environ.get("MAX_DISTANCE", "0.6"))

bq = bigquery.Client(project=PROJECT)
llm = genai.Client(vertexai=True, project=PROJECT, location=os.environ["VERTEX_LOCATION"])

# Una sola consulta: genera el embedding de la pregunta DENTRO de BigQuery y busca los vecinos
RETRIEVE_SQL = f"""
SELECT base.source, base.content, distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT}.{DATASET}.chunks`, 'embedding',
  (SELECT ml_generate_embedding_result AS embedding
   FROM ML.GENERATE_EMBEDDING(MODEL `{PROJECT}.{DATASET}.embedding_model`,
                              (SELECT @question AS content),
                              STRUCT('RETRIEVAL_QUERY' AS task_type, TRUE AS flatten_json_output))),
  top_k => @top_k, distance_type => 'COSINE')
WHERE distance <= @max_distance
ORDER BY distance
"""

SYSTEM = (
    "Eres un asistente de la empresa. Responde SOLO con la información del CONTEXTO. "
    "Cita la fuente entre corchetes después de cada dato, p. ej. [vacaciones.md]. "
    "Si el contexto no contiene la respuesta, responde exactamente: No tengo esa información."
)


def retrieve(question):
    job = bq.query(RETRIEVE_SQL, job_config=bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter("question", "STRING", question),
        bigquery.ScalarQueryParameter("top_k", "INT64", TOP_K),
        bigquery.ScalarQueryParameter("max_distance", "FLOAT64", MAX_DISTANCE),
    ]))
    return [dict(row) for row in job.result()]


@functions_framework.http
def handler(request):
    question = ((request.get_json(silent=True) or {}).get("question") or "").strip()
    if not question:
        return ({"error": "question es requerido"}, 400)

    chunks = retrieve(question)
    context = "\n\n".join(f"[{c['source']}] {c['content']}" for c in chunks) or "(sin resultados)"

    response = llm.models.generate_content(
        model=os.environ["MODEL"],
        contents=f"CONTEXTO:\n{context}\n\nPREGUNTA: {question}",
        config=types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0.1, max_output_tokens=500),
    )

    usage = response.usage_metadata
    logging.info(json.dumps({"severity": "INFO", "question_chars": len(question), "chunks": len(chunks),
                             "input_tokens": usage.prompt_token_count, "output_tokens": usage.candidates_token_count}))
    return {
        "answer": response.text,
        "sources": [{"source": c["source"], "distance": round(c["distance"], 4)} for c in chunks],
        "usage": {"input_tokens": usage.prompt_token_count, "output_tokens": usage.candidates_token_count},
    }
