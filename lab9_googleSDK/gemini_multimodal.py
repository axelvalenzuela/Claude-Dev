"""
Lab 9 - Multimodal: imagen + texto en el mismo prompt

Gemini entiende imagenes, PDF, audio y video. Dos formas de mandar un archivo:
    - Vertex AI: por URI de Cloud Storage (gs://...), sin subir bytes desde tu PC.
    - Gemini API: los bytes directamente (o con la Files API para archivos grandes).
"""

import urllib.request

from google.genai import types

from comun import MODELO, USA_VERTEX, crear_cliente

IMAGEN_GCS = "gs://cloud-samples-data/generative-ai/image/scones.jpg"
IMAGEN_HTTPS = "https://storage.googleapis.com/cloud-samples-data/generative-ai/image/scones.jpg"

client = crear_cliente()

if USA_VERTEX:
    imagen = types.Part.from_uri(file_uri=IMAGEN_GCS, mime_type="image/jpeg")
else:
    with urllib.request.urlopen(IMAGEN_HTTPS) as r:
        imagen = types.Part.from_bytes(data=r.read(), mime_type="image/jpeg")

response = client.models.generate_content(
    model=MODELO,
    contents=[imagen, "Describe the image in 3 bullet points and estimate how many calories are on the plate."],
)
print(response.text)
