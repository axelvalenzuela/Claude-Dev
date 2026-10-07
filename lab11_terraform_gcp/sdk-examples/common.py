"""Configuración compartida por los ejemplos (todo se ajusta con variables de entorno).

Autenticación: gcloud auth application-default login (sin llaves JSON).
"""

import math
import os

from google import genai
from google.genai import types

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")

client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)


def ask(prompt, system=None, max_tokens=400):
    """Atajo: una pregunta, una respuesta (usado por varios ejemplos)."""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system, max_output_tokens=max_tokens, temperature=0.2),
    )
    return response.text, response.usage_metadata


def embed(text, task="RETRIEVAL_DOCUMENT"):
    """Vector de embeddings. task: RETRIEVAL_DOCUMENT para documentos, RETRIEVAL_QUERY para preguntas."""
    response = client.models.embed_content(
        model=EMBED_MODEL, contents=text, config=types.EmbedContentConfig(task_type=task, output_dimensionality=256)
    )
    return response.embeddings[0].values


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))
