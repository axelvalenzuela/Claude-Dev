"""Unit tests for src/chunking.py — pure Python, no GCP credentials needed.

Run with: pytest tests/test_chunking.py -v
"""
from src.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_is_a_single_chunk():
    text = "hola mundo esto es corto"
    chunks = chunk_text(text, chunk_size=180, overlap=40)
    assert chunks == [text]


def test_long_text_is_split_with_overlap():
    words = [f"palabra{i}" for i in range(500)]
    text = " ".join(words)

    chunks = chunk_text(text, chunk_size=180, overlap=40)

    # step = 180 - 40 = 140, so chunks start at word 0, 140, 280, 420.
    assert len(chunks) == 4
    assert chunks[0].split()[0] == "palabra0"
    assert chunks[0].split()[-1] == "palabra179"
    # The last 40 words of chunk 0 (140..179) must reappear at the start
    # of chunk 1 — that's the overlap the docstring promises.
    assert chunks[1].split()[:40] == chunks[0].split()[-40:]


def test_no_words_are_lost():
    words = [f"w{i}" for i in range(233)]  # an awkward, non-round count
    text = " ".join(words)

    chunks = chunk_text(text, chunk_size=180, overlap=40)

    seen = set()
    for chunk in chunks:
        seen.update(chunk.split())
    assert seen == set(words)


def test_overlap_zero_gives_contiguous_chunks():
    words = [f"w{i}" for i in range(20)]
    text = " ".join(words)

    chunks = chunk_text(text, chunk_size=10, overlap=0)

    assert chunks == ["w0 w1 w2 w3 w4 w5 w6 w7 w8 w9", "w10 w11 w12 w13 w14 w15 w16 w17 w18 w19"]
