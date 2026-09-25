"""Builds the local vector index from data/docs/*.md.

Two ways to run this:
  1. Manually, once, from the CLI:  python -m src.ingest
  2. Automatically, on first request, from src/main.py's startup hook —
     so a fresh checkout or a fresh Cloud Run container "just works"
     without a manual step. See INSTRUCCIONES.md for both paths.

Both call the same build_index() function below, so there is exactly one
place that defines how chunking and embedding happen.
"""
from __future__ import annotations

import logging
from pathlib import Path

from src.chunking import chunk_text
from src.config import settings
from src.gemini_client import embed_texts
from src.vector_store import Chunk, VectorStore

logger = logging.getLogger(__name__)


def load_documents(docs_dir: Path) -> list[tuple[str, str]]:
    """Return [(filename, full_text), ...] for every markdown file, sorted
    by filename so the index is built in a deterministic, reproducible
    order (helps when diffing chunks.json across runs)."""
    paths = sorted(docs_dir.glob("*.md"))
    if not paths:
        raise FileNotFoundError(
            f"No se encontraron archivos .md en {docs_dir}. "
            "¿Corriste esto desde la raíz de lab7?"
        )
    return [(p.name, p.read_text(encoding="utf-8")) for p in paths]


def build_index(docs_dir: Path | None = None, index_dir: Path | None = None) -> VectorStore:
    """Read every doc, chunk it, embed all chunks in one batch call, and
    persist the result. Returns the in-memory VectorStore too, so
    src/main.py can use it immediately without re-reading it from disk."""
    docs_dir = docs_dir or settings.docs_dir
    index_dir = index_dir or settings.index_dir

    documents = load_documents(docs_dir)
    logger.info("Ingesting %d documents from %s", len(documents), docs_dir)

    all_chunks: list[Chunk] = []
    for filename, text in documents:
        for i, piece in enumerate(chunk_text(text)):
            all_chunks.append(Chunk(text=piece, source=filename, chunk_index=i))

    logger.info("Split into %d chunks, embedding in one batch call...", len(all_chunks))
    # One API call for all chunks instead of one call per chunk: fewer
    # round trips, and Vertex AI's embedding endpoint accepts batches.
    embeddings = embed_texts([c.text for c in all_chunks], task_type="RETRIEVAL_DOCUMENT")

    store = VectorStore(chunks=all_chunks, embeddings=embeddings)
    store.save(index_dir)
    logger.info("Index saved to %s", index_dir)
    return store


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build_index()
