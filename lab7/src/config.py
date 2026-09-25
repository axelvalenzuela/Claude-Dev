"""Central place for every setting this app reads from the environment.

Nothing else in src/ should call os.getenv() directly — importing `settings`
from here keeps all the environment-variable names in one file, and makes
it obvious (via the error below) when the required GCP settings are
missing, instead of failing deep inside a Vertex AI call.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Loads .env into os.environ for local development. In Cloud Run there is
# no .env file (it's in .gitignore, never deployed) — real environment
# variables set with `--set-env-vars` take over instead, and load_dotenv()
# is a harmless no-op there because it finds no .env to load.
load_dotenv()

# Repo layout: lab7/src/config.py -> lab7/
BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    gcp_project_id: str
    gcp_location: str
    embedding_model: str
    generation_model: str
    rag_top_k: int
    docs_dir: Path
    index_dir: Path
    port: int


def _load_settings() -> Settings:
    project_id = os.environ.get("GCP_PROJECT_ID", "")
    if not project_id or project_id == "tu-proyecto-gcp":
        # Fail loudly and early instead of letting the Vertex AI client
        # raise a confusing auth/permission error later. See
        # INSTRUCCIONES.md step 3 for how to set this.
        raise RuntimeError(
            "GCP_PROJECT_ID no está configurado. Copia .env.example a .env "
            "y pon el id de tu proyecto GCP (no el nombre ni el número)."
        )

    return Settings(
        gcp_project_id=project_id,
        gcp_location=os.environ.get("GCP_LOCATION", "us-central1"),
        embedding_model=os.environ.get("EMBEDDING_MODEL", "text-embedding-005"),
        generation_model=os.environ.get("GENERATION_MODEL", "gemini-2.5-flash"),
        rag_top_k=int(os.environ.get("RAG_TOP_K", "4")),
        docs_dir=BASE_DIR / "data" / "docs",
        index_dir=BASE_DIR / "data" / "index",
        port=int(os.environ.get("PORT", "8080")),
    )


settings = _load_settings()
