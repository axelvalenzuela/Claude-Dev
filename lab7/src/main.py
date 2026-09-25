"""FastAPI app: serves the chat page and the /api/chat endpoint.

Route order matters here: the /api/* routes are registered BEFORE
app.mount("/", ...), so FastAPI tries them first and only falls back to
serving static files from web/ for anything else (including "/", which
StaticFiles(html=True) resolves to web/index.html automatically).
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config import BASE_DIR, settings
from src.ingest import build_index
from src.rag_engine import RagEngine
from src.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Holds the loaded RagEngine. A dict (not a bare global) so lifespan() can
# populate it without a `global` statement — see FastAPI's lifespan docs.
state: dict[str, RagEngine] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the index on first startup if it's not on disk yet (fresh
    # checkout, or a fresh Cloud Run container that only ships data/docs/,
    # not a prebuilt index — see Dockerfile and INSTRUCCIONES.md). This
    # makes the app self-contained: no separate "run ingest" step is
    # *required*, though doing it manually first is faster to iterate on.
    if not VectorStore.exists(settings.index_dir):
        logger.info("No index found at %s, building it now...", settings.index_dir)
        build_index()
    state["rag_engine"] = RagEngine.load()
    logger.info("RAG engine ready.")
    yield
    state.clear()


app = FastAPI(title="Lab7 - Agente de Consulta (RAG sobre Vertex AI Gemini)", lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str
    use_rag: bool = True


class ChatResponse(BaseModel):
    answer: str
    used_rag: bool
    sources: list[str]


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")

    engine = state.get("rag_engine")
    if engine is None:
        # Should not happen in practice (lifespan sets it before the app
        # accepts traffic), but fails clearly instead of a bare 500 if it does.
        raise HTTPException(status_code=503, detail="El motor RAG todavía no está listo.")

    try:
        result = engine.answer(question, use_rag=request.use_rag)
    except Exception:
        logger.exception("Error generando respuesta")
        raise HTTPException(
            status_code=502,
            detail="Error al llamar a Vertex AI. Revisa credenciales/permisos (ver INSTRUCCIONES.md).",
        )

    return ChatResponse(answer=result.answer, used_rag=result.used_rag, sources=result.sources)


# Registered last on purpose (see module docstring): this catches "/" and
# every other path not matched above, serving web/index.html, web/app.js,
# web/style.css as plain static files.
app.mount("/", StaticFiles(directory=BASE_DIR / "web", html=True), name="web")
