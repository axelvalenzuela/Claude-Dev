"""A deliberately simple vector store: a NumPy matrix plus a JSON file.

This is the "basic exercise" version of what Vertex AI Vector Search or a
database like AlloyDB/Cloud SQL with pgvector would do at production
scale. It works fine up to a few thousand chunks (this lab has a few
dozen) because it just computes cosine similarity against every row —
no index, no approximate search, no persistence layer beyond two local
files. See CONCEPTOS.md for when to graduate to a real vector database.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Chunk:
    """One retrievable unit of text plus where it came from."""

    text: str
    source: str  # e.g. "02_arquitectura_gcp.md"
    chunk_index: int  # position of this chunk within its source document


@dataclass
class SearchResult:
    chunk: Chunk
    score: float  # cosine similarity, higher is more relevant (max 1.0)


class VectorStore:
    """Holds chunks and their embeddings, and answers similarity searches."""

    def __init__(self, chunks: list[Chunk], embeddings: np.ndarray):
        if len(chunks) != embeddings.shape[0]:
            raise ValueError(
                f"{len(chunks)} chunks but {embeddings.shape[0]} embedding rows"
            )
        self.chunks = chunks
        # Normalizing once at build time turns "cosine similarity" into a
        # plain dot product at search time (a x b when both are unit
        # vectors), which is cheaper to compute per query.
        self.embeddings = _normalize_rows(embeddings)

    def search(self, query_embedding: np.ndarray, k: int) -> list[SearchResult]:
        """Return the k chunks whose embeddings are closest to the query."""
        if len(self.chunks) == 0:
            return []

        query_unit = _normalize_rows(query_embedding.reshape(1, -1))[0]
        # Dot product of every (unit) row against the (unit) query vector
        # == cosine similarity of every chunk against the query.
        scores = self.embeddings @ query_unit

        k = min(k, len(self.chunks))
        # argpartition is O(n) instead of a full O(n log n) sort — fine to
        # skip at this scale, but it's the right habit for when the store
        # grows past a few thousand rows.
        top_indices = np.argpartition(-scores, k - 1)[:k]
        top_indices = top_indices[np.argsort(-scores[top_indices])]

        return [
            SearchResult(chunk=self.chunks[i], score=float(scores[i]))
            for i in top_indices
        ]

    def save(self, index_dir: Path) -> None:
        """Persist to <index_dir>/embeddings.npy + <index_dir>/chunks.json."""
        index_dir.mkdir(parents=True, exist_ok=True)
        np.save(index_dir / "embeddings.npy", self.embeddings)
        metadata = [
            {"text": c.text, "source": c.source, "chunk_index": c.chunk_index}
            for c in self.chunks
        ]
        (index_dir / "chunks.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, index_dir: Path) -> "VectorStore":
        embeddings = np.load(index_dir / "embeddings.npy")
        metadata = json.loads((index_dir / "chunks.json").read_text(encoding="utf-8"))
        chunks = [
            Chunk(text=m["text"], source=m["source"], chunk_index=m["chunk_index"])
            for m in metadata
        ]
        store = cls.__new__(cls)  # skip __init__'s re-normalization; already unit vectors
        store.chunks = chunks
        store.embeddings = embeddings
        return store

    @staticmethod
    def exists(index_dir: Path) -> bool:
        return (index_dir / "embeddings.npy").exists() and (index_dir / "chunks.json").exists()


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    """Scale every row to unit length, guarding against division by zero."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms
