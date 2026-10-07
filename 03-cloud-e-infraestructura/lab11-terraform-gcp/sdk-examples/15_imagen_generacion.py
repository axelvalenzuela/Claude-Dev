"""15 · Generación de imágenes con Imagen en Vertex AI.

Concepto: el mismo SDK genera imágenes. Las imágenes generadas llevan marca de agua digital
(SynthID) y pasan por filtros de seguridad; el prompt y la relación de aspecto controlan el resultado.

    python 15_imagen_generacion.py "un servidor en la nube como una caricatura de estilo plano"
"""

import os
import sys

from google.genai import types

from common import client

prompt = sys.argv[1] if len(sys.argv) > 1 else "Diagrama isométrico minimalista de un pipeline de datos en la nube, colores azul y verde"

response = client.models.generate_images(
    model=os.environ.get("IMAGEN_MODEL", "imagen-4.0-generate-001"),
    prompt=prompt,
    config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9"),
)

for i, generated in enumerate(response.generated_images):
    path = f"imagen_{i}.png"
    generated.image.save(path)
    print("Guardada:", path)
