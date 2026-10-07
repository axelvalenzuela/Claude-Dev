"""Pure text-chunking logic, split out from ingest.py on purpose.

This module has zero dependencies on Vertex AI or even on src/config.py,
so it can be unit-tested (tests/test_chunking.py) without GCP credentials,
network access, or an API key of any kind — the whole point of keeping
"split text into pieces" separate from "call an embedding model".
"""
from __future__ import annotations

# Word-based chunking (not token-based): simple, dependency-free, and good
# enough for markdown docs of this size. CHUNK_OVERLAP_WORDS repeats the
# tail of one chunk at the start of the next so a sentence that straddles
# a chunk boundary still appears whole in at least one chunk.
CHUNK_SIZE_WORDS = 180
CHUNK_OVERLAP_WORDS = 40


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    """Split text into overlapping word-count windows.

    With the defaults, each chunk is 180 words and the next one starts 140
    words later (step = chunk_size - overlap), so the last 40 words of one
    chunk are repeated as the first 40 words of the next. That overlap is
    what keeps a sentence sitting right on a chunk boundary from being cut
    in half with no chunk that contains it whole.
    """
    words = text.split()
    if not words:
        return []

    step = chunk_size - overlap if overlap < chunk_size else chunk_size
    chunks = []
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
    return chunks
