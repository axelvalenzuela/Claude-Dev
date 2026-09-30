"""Envoltura delgada (thin wrapper) sobre la API de Gemini en Vertex AI
(a traves del SDK google-genai).

Este es el UNICO archivo del proyecto que habla directamente con Vertex AI.
Todo lo demas (vector_store.py, rag_engine.py) trabaja con listas/arrays de
Python puro, lo que permite probar esas piezas sin necesitar credenciales
de GCP — ver tests/test_vector_store.py.

Autenticacion: este archivo nunca maneja credenciales por si mismo. El SDK
usa Application Default Credentials (ADC) automaticamente:
  - Desarrollo local: `gcloud auth application-default login` (ver INSTRUCCIONES.md)
  - Cloud Run: la cuenta de servicio asociada al servicio, de forma automatica
"""
from __future__ import annotations

import numpy as np
from google import genai
from google.genai import types

from src.config import settings

# Un solo cliente para todo el proceso. vertexai=True es lo que hace que esto
# llame a Vertex AI (con alcance a un project/location, facturado a tu proyecto
# de GCP) en lugar de la Gemini Developer API publica (que usa una API key
# separada).
_client = genai.Client(
    vertexai=True,
    project=settings.gcp_project_id,
    location=settings.gcp_location,
)


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> np.ndarray:
    """Convierte una lista de strings en una matriz de vectores de embedding.

    task_type importa: si se va a guardar un documento se debe usar
    RETRIEVAL_DOCUMENT, mientras que si se embebe la pregunta de un usuario
    para buscar se debe usar RETRIEVAL_QUERY. El modelo acomoda ambos casos
    en un espacio donde el vector de la consulta termina cerca de los
    documentos que la responden — usar el task_type incorrecto en alguno de
    los dos lados degrada silenciosamente la calidad de la busqueda sin
    lanzar ningun error, asi que quien llame a esta funcion siempre debe
    pasar el correcto.

    Retorna un arreglo float32 de forma (len(texts), embedding_dim).
    """
    if not texts:
        return np.zeros((0, 0), dtype="float32")

    response = _client.models.embed_content(
        model=settings.embedding_model,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    vectors = [embedding.values for embedding in response.embeddings]
    return np.array(vectors, dtype="float32")


def generate_answer(prompt: str, temperature: float = 0.2) -> str:
    """Le pide a Gemini que genere texto para un prompt ya construido.

    La temperatura baja (0.2) es a proposito: esta app responde preguntas
    factuales sobre documentacion interna, no hace lluvia de ideas, asi que
    se busca respuestas consistentes y ancladas en los hechos en vez de
    respuestas creativas.
    """
    text, _usage = generate_answer_with_usage(prompt, temperature)
    return text


def generate_answer_with_usage(
    prompt: str, temperature: float = 0.2
) -> tuple[str, types.GenerateContentResponseUsageMetadata]:
    """Es la misma llamada que generate_answer, pero ademas retorna el
    usage_metadata — los conteos reales de tokens (prompt, respuesta y
    total) que Vertex AI facturo por esta llamada. Ver src/count_tokens.py
    para un CLI que los imprime."""
    response = _client.models.generate_content(
        model=settings.generation_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=1024,
        ),
    )
    return response.text or "", response.usage_metadata


def count_tokens(text: str, model: str | None = None) -> int:
    """Cuenta cuantos tokens usaria `text` para `model` (por defecto: el
    modelo de generacion) SIN llamar a generate_content — es gratis, no
    consume cuota. Sirve para presupuestar un prompt (ventana de contexto,
    costo) antes de enviarlo de verdad."""
    response = _client.models.count_tokens(model=model or settings.generation_model, contents=text)
    return response.total_tokens
