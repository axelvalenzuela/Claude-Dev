"""Respuestas fundamentadas (grounded) sobre documentos indexados en Vertex AI Search.

POST {"question": "...", "mode": "gemini" | "search"}
  gemini: Gemini decide qué buscar con la herramienta Retrieval(VertexAISearch) y devuelve grounding_metadata
  search: la Search API devuelve resultados + un resumen generado por el motor con citas
"""

import os

import functions_framework
from google import genai
from google.cloud import discoveryengine_v1 as de
from google.genai import types

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
LOC = os.environ["SEARCH_LOCATION"]
DATA_STORE = f"projects/{PROJECT}/locations/{LOC}/collections/default_collection/dataStores/{os.environ['DATA_STORE_ID']}"
SERVING_CONFIG = (f"projects/{PROJECT}/locations/{LOC}/collections/default_collection/"
                  f"engines/{os.environ['ENGINE_ID']}/servingConfigs/default_search")

llm = genai.Client(vertexai=True, project=PROJECT, location=os.environ["VERTEX_LOCATION"])
endpoint = None if LOC == "global" else {"api_endpoint": f"{LOC}-discoveryengine.googleapis.com"}
search_client = de.SearchServiceClient(client_options=endpoint)


def gemini_grounded(question):
    response = llm.models.generate_content(
        model=os.environ["MODEL"],
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction="Responde en español usando solo los documentos recuperados. Si no hay información, dilo.",
            tools=[types.Tool(retrieval=types.Retrieval(vertex_ai_search=types.VertexAISearch(datastore=DATA_STORE)))],
            temperature=0.1,
        ),
    )
    meta = response.candidates[0].grounding_metadata
    sources = sorted({c.retrieved_context.title or c.retrieved_context.uri for c in (meta.grounding_chunks or [])
                      if c.retrieved_context}) if meta else []
    supports = len(meta.grounding_supports or []) if meta else 0
    return {"answer": response.text, "sources": sources, "grounding_supports": supports,
            "usage": {"input_tokens": response.usage_metadata.prompt_token_count,
                      "output_tokens": response.usage_metadata.candidates_token_count}}


def engine_search(question):
    request = de.SearchRequest(
        serving_config=SERVING_CONFIG,
        query=question,
        page_size=3,
        content_search_spec=de.SearchRequest.ContentSearchSpec(
            snippet_spec=de.SearchRequest.ContentSearchSpec.SnippetSpec(return_snippet=True),
            summary_spec=de.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=3, include_citations=True, ignore_non_summary_seeking_query=True,
                language_code="es"),
        ),
    )
    response = search_client.search(request)
    results = [r.document.derived_struct_data.get("link", r.document.id) for r in response.results]
    return {"answer": response.summary.summary_text, "sources": results}


@functions_framework.http
def handler(request):
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return ({"error": "question es requerido"}, 400)
    mode = body.get("mode", "gemini")
    return gemini_grounded(question) if mode == "gemini" else engine_search(question)
