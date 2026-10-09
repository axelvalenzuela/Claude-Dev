"""07 · Multimodal: imagen + texto en la misma petición.

Concepto: Gemini es nativamente multimodal. Una imagen en Cloud Storage se pasa por URI
(no se descarga ni se codifica); también puedes pasar bytes locales con Part.from_bytes.

    python 07_gemini_multimodal.py                     # imagen pública de ejemplo de Google
    python 07_gemini_multimodal.py gs://tu-bucket/foto.jpg
"""

import sys

from google.genai import types

from common import MODEL, client

uri = sys.argv[1] if len(sys.argv) > 1 else "gs://cloud-samples-data/generative-ai/image/scones.jpg"

response = client.models.generate_content(
    model=MODEL,
    contents=[
        types.Part.from_uri(file_uri=uri, mime_type="image/jpeg"),
        "Describe la imagen en 2 líneas y lista los objetos que aparecen en formato de viñetas.",
    ],
)

print(response.text)
print("\nTokens de entrada (la imagen cuenta como tokens):", response.usage_metadata.prompt_token_count)
