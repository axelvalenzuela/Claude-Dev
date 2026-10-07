"""The actual "RAG" in this lab: retrieve relevant chunks, then generate.

This is intentionally the smallest possible RAG loop:

    question -> embed -> search vector store -> top-k chunks
             -> build a prompt that includes those chunks as context
             -> Gemini generates the answer grounded in them

`answer(question, use_rag=False)` also exists so the web page can toggle
RAG on/off and show, side by side, how ungrounded Gemini either declines
to answer or makes something up about facts that only exist in
data/docs/ (the fictional Programa Helios) — that comparison is the best
way to *see* why RAG helps, more than reading about it.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.config import settings
from src.gemini_client import embed_texts, generate_answer
from src.vector_store import SearchResult, VectorStore

SYSTEM_PROMPT = """Eres el Agente de Consulta del Programa Helios de Acme \
Analytics. Respondes preguntas sobre la migración de SAS a Python/GCP \
usando ÚNICAMENTE la información del CONTEXTO de abajo.

Reglas:
- Si el CONTEXTO no contiene la respuesta, di exactamente que no tienes \
esa información en la documentación del programa. No inventes datos, \
números ni nombres que no aparezcan en el CONTEXTO.
- Sé conciso: 2 a 5 frases.
- Si es útil, cita de qué documento sacaste el dato (aparece como \
"Fuente: <archivo>" en cada bloque de contexto).
"""


@dataclass
class RagAnswer:
    answer: str
    used_rag: bool
    sources: list[str]  # e.g. ["02_arquitectura_gcp.md", "04_faq_agentes.md"]


class RagEngine:
    def __init__(self, store: VectorStore):
        self._store = store

    @classmethod
    def load(cls) -> "RagEngine":
        if not VectorStore.exists(settings.index_dir):
            raise FileNotFoundError(
                f"No hay índice en {settings.index_dir}. Corre "
                "`python -m src.ingest` primero, o simplemente arranca la "
                "app: src/main.py lo construye solo si falta."
            )
        return cls(VectorStore.load(settings.index_dir))

    def retrieve(self, question: str, k: int | None = None) -> list[SearchResult]:
        k = k or settings.rag_top_k
        # RETRIEVAL_QUERY, not RETRIEVAL_DOCUMENT: same model, different
        # task_type, so the question lands close to the chunks that answer
        # it in embedding space. See gemini_client.embed_texts docstring.
        query_embedding = embed_texts([question], task_type="RETRIEVAL_QUERY")[0]
        return self._store.search(query_embedding, k)

    def answer(self, question: str, use_rag: bool = True) -> RagAnswer:
        if not use_rag:
            # Ask Gemini directly, with no access to data/docs/, so the UI
            # can show what happens without retrieval: either a refusal to
            # guess, or a plausible-sounding but wrong/generic answer about
            # a fictional internal program it was never trained on.
            text = generate_answer(
                f"{question}\n\n(Responde en 2-5 frases. Si no sabes la "
                "respuesta con certeza, dilo explícitamente en vez de "
                "adivinar.)"
            )
            return RagAnswer(answer=text, used_rag=False, sources=[])

        results = self.retrieve(question)
        prompt = self._build_prompt(question, results)
        text = generate_answer(prompt)
        sources = sorted({r.chunk.source for r in results})
        return RagAnswer(answer=text, used_rag=True, sources=sources)

    @staticmethod
    def _build_prompt(question: str, results: list[SearchResult]) -> str:
        context_blocks = "\n\n".join(
            f"Fuente: {r.chunk.source}\n{r.chunk.text}" for r in results
        )
        return (
            f"{SYSTEM_PROMPT}\n\nCONTEXTO:\n{context_blocks}\n\n"
            f"PREGUNTA: {question}"
        )
