"""
Lab 9 - Grounding con Google Search

El conocimiento del modelo tiene fecha de corte. Con la herramienta google_search,
Gemini busca en la web, responde con informacion actual y devuelve las fuentes en
grounding_metadata. Reduce alucinaciones en preguntas sobre hechos recientes.

Nota: el grounding se cobra aparte (por consulta). En Vertex AI tambien existe grounding
con tus propios datos (Vertex AI Search / RAG Engine) en lugar de la web publica.
"""

from google.genai import types

from comun import MODELO, crear_cliente

client = crear_cliente()

response = client.models.generate_content(
    model=MODELO,
    contents="¿Cuál es la película más reciente de Marvel Studios que se estrenó en cines y cuándo fue?",
    config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())]),
)

print(response.text)

metadata = response.candidates[0].grounding_metadata
if metadata is None:
    print("\n(El modelo respondió sin buscar en la web.)")
else:
    print("\nBúsquedas que hizo:", metadata.web_search_queries)
    print("Fuentes:")
    for i, chunk in enumerate(metadata.grounding_chunks or [], start=1):
        if chunk.web:
            print(f"  [{i}] {chunk.web.title} - {chunk.web.uri}")
