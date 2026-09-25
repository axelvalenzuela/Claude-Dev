"""Thin wrapper around the Vertex AI Gemini API (via the google-genai SDK).

This is the ONLY file in the project that talks to Vertex AI directly.
Everything else (vector_store.py, rag_engine.py) works with plain Python
lists/arrays, which makes those pieces testable without any GCP
credentials — see tests/test_vector_store.py.

Authentication: this file never handles credentials itself. The SDK uses
Application Default Credentials (ADC) automatically:
  - Local dev: `gcloud auth application-default login` (see INSTRUCCIONES.md)
  - Cloud Run: the service's attached service account, automatically
"""
from __future__ import annotations

import numpy as np
from google import genai
from google.genai import types

from src.config import settings

# One client for the whole process. vertexai=True is what makes this call
# Vertex AI (project/location-scoped, billed to your GCP project) instead
# of the public Gemini Developer API (which uses a separate API key).
_client = genai.Client(
    vertexai=True,
    project=settings.gcp_project_id,
    location=settings.gcp_location,
)


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> np.ndarray:
    """Turn a list of strings into a matrix of embedding vectors.

    task_type matters: embedding a document to store it should use
    RETRIEVAL_DOCUMENT, while embedding a user's question to search should
    use RETRIEVAL_QUERY. The model nudges the two into a space where a
    query vector ends up close to the documents that answer it — using the
    wrong task_type for one side quietly hurts retrieval quality without
    raising an error, so callers must always pass the right one.

    Returns an (len(texts), embedding_dim) float32 array.
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
    """Ask Gemini to generate text for a single already-built prompt.

    Low temperature (0.2) on purpose: this app is answering factual
    questions about internal documentation, not brainstorming, so we want
    consistent, grounded answers rather than creative ones.
    """
    text, _usage = generate_answer_with_usage(prompt, temperature)
    return text


def generate_answer_with_usage(
    prompt: str, temperature: float = 0.2
) -> tuple[str, types.GenerateContentResponseUsageMetadata]:
    """Same call as generate_answer, but also returns usage_metadata — the
    actual prompt/response/total token counts Vertex AI billed for this
    call. See src/count_tokens.py for a CLI that prints it."""
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
    """Count how many tokens `text` would use for `model` (default: the
    generation model) WITHOUT calling generate_content — free, no quota
    spent. Useful to budget a prompt (context window, cost) before sending
    it for real."""
    response = _client.models.count_tokens(model=model or settings.generation_model, contents=text)
    return response.total_tokens
