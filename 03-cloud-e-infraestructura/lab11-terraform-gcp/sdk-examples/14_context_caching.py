"""14 · Context caching: reutilizar un contexto grande con descuento.

Concepto: si muchas preguntas comparten el mismo contexto largo (manual, contrato, código),
se cachea una vez y cada pregunta solo paga los tokens nuevos; los tokens cacheados cuestan menos.
Requiere un contexto mínimo (miles de tokens) y tiene TTL (se cobra el almacenamiento por hora).

    python 14_context_caching.py
"""

from google.genai import types

from common import MODEL, client

# Contexto grande de ejemplo: un PDF público de Google (también puedes usar texto o tus archivos en GCS)
document = types.Part.from_uri(file_uri="gs://cloud-samples-data/generative-ai/pdf/2312.11805v3.pdf",
                               mime_type="application/pdf")

cache = client.caches.create(
    model=MODEL,
    config=types.CreateCachedContentConfig(
        contents=[types.Content(role="user", parts=[document])],
        system_instruction="Responde preguntas sobre el documento en español, en 2 líneas.",
        ttl="600s",
    ),
)
print("Cache:", cache.name, "· tokens cacheados:", cache.usage_metadata.total_token_count)

for question in ["¿De qué trata el documento?", "¿Qué tamaños de modelo menciona?"]:
    response = client.models.generate_content(
        model=MODEL, contents=question, config=types.GenerateContentConfig(cached_content=cache.name))
    u = response.usage_metadata
    print(f"\n> {question}\n{response.text}\n  [entrada total: {u.prompt_token_count} · desde caché: {u.cached_content_token_count}]")

client.caches.delete(name=cache.name)   # no pagues almacenamiento de más
