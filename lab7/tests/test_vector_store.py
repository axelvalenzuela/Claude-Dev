"""Unit tests for src/vector_store.py — pure NumPy math, no GCP
credentials or network access needed.

Run with: pytest tests/test_vector_store.py -v
"""
import tempfile
from pathlib import Path

import numpy as np

from src.vector_store import Chunk, VectorStore


def _fake_store() -> VectorStore:
    # Three orthogonal-ish 3D vectors, easy to reason about by hand.
    chunks = [
        Chunk(text="habla de vacaciones", source="a.md", chunk_index=0),
        Chunk(text="habla de VPN", source="b.md", chunk_index=0),
        Chunk(text="tambien habla de vacaciones", source="c.md", chunk_index=0),
    ]
    embeddings = np.array(
        [
            [1.0, 0.0, 0.0],  # a.md: "vacaciones" axis
            [0.0, 1.0, 0.0],  # b.md: "VPN" axis, orthogonal to a.md
            [0.9, 0.1, 0.0],  # c.md: mostly "vacaciones", close to a.md
        ],
        dtype="float32",
    )
    return VectorStore(chunks=chunks, embeddings=embeddings)


def test_search_ranks_closest_vectors_first():
    store = _fake_store()
    query = np.array([1.0, 0.0, 0.0], dtype="float32")  # pure "vacaciones"

    results = store.search(query, k=3)

    assert [r.chunk.source for r in results] == ["a.md", "c.md", "b.md"]
    # a.md is an exact match to the query direction -> similarity ~1.0
    assert results[0].score > 0.99
    # b.md is orthogonal to the query -> similarity ~0.0
    assert abs(results[-1].score) < 0.01


def test_search_respects_k():
    store = _fake_store()
    query = np.array([1.0, 0.0, 0.0], dtype="float32")

    results = store.search(query, k=1)

    assert len(results) == 1
    assert results[0].chunk.source == "a.md"


def test_search_on_empty_store_returns_empty_list():
    store = VectorStore(chunks=[], embeddings=np.zeros((0, 3), dtype="float32"))
    results = store.search(np.array([1.0, 0.0, 0.0], dtype="float32"), k=5)
    assert results == []


def test_save_and_load_round_trip():
    store = _fake_store()
    with tempfile.TemporaryDirectory() as tmp:
        index_dir = Path(tmp) / "index"
        store.save(index_dir)

        assert (index_dir / "embeddings.npy").exists()
        assert (index_dir / "chunks.json").exists()
        assert VectorStore.exists(index_dir)

        loaded = VectorStore.load(index_dir)

    assert [c.source for c in loaded.chunks] == [c.source for c in store.chunks]
    assert loaded.embeddings.shape == store.embeddings.shape

    query = np.array([0.0, 1.0, 0.0], dtype="float32")  # pure "VPN"
    results = loaded.search(query, k=1)
    assert results[0].chunk.source == "b.md"
