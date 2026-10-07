"""13 · Grounding con Google Search: respuestas con información actual y fuentes.

Concepto: el conocimiento del modelo tiene fecha de corte. Con la herramienta google_search,
Gemini busca en la web, responde y devuelve grounding_metadata con las fuentes y las búsquedas usadas.

    python 13_grounding_google_search.py "¿Cuál es la versión más reciente de Terraform?"
"""

import sys

from google.genai import types

from common import MODEL, client

question = sys.argv[1] if len(sys.argv) > 1 else "¿Qué anunció Google Cloud esta semana sobre Gemini?"

response = client.models.generate_content(
    model=MODEL,
    contents=question,
    config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())]),
)

print(response.text, "\n")
meta = response.candidates[0].grounding_metadata
if meta:
    print("Búsquedas realizadas:", meta.web_search_queries)
    for chunk in meta.grounding_chunks or []:
        print(" -", chunk.web.title, chunk.web.uri)
