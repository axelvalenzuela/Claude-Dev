"""Configuración leída de variables de entorno (o del archivo .env).

MODO=simulado (por defecto)  -> nada sale a internet, costo $0.
MODO=real                    -> llama a Vertex AI con tu proyecto de GCP.

Buenas prácticas que se ven aquí:
  * Nada de secretos ni ids de proyecto escritos en el código.
  * El .env solo existe en tu máquina (está en .gitignore). En Cloud Run /
    Cloud Functions las mismas variables se pasan con --set-env-vars.
  * Si falta algo obligatorio, se falla PRONTO y con un mensaje claro.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]      # carpeta 04-vertex-ai-projects/

try:
    from dotenv import load_dotenv

    load_dotenv(RAIZ / ".env")
except ImportError:      # python-dotenv es opcional: sin él solo se leen variables reales
    pass


@dataclass(frozen=True)
class Config:
    modo: str
    proyecto: str
    region: str
    region_modelos: str
    region_embeddings: str
    modelo: str
    modelo_embeddings: str
    bucket: str
    dataset: str

    @property
    def es_real(self) -> bool:
        return self.modo == "real"

    def exigir_proyecto(self) -> None:
        """Llamar antes de cualquier operación que toque GCP."""
        if not self.proyecto or self.proyecto == "tu-proyecto-gcp":
            raise SystemExit(
                "Falta GCP_PROJECT_ID en 04-vertex-ai-projects/.env (o estás en MODO=simulado).\n"
                "Ver docs/gcp-connect.md, paso 3."
            )


def cargar() -> Config:
    modo = os.getenv("MODO", "simulado").strip().lower()
    if modo not in ("simulado", "real"):
        raise SystemExit(f"MODO debe ser 'simulado' o 'real', no '{modo}'")
    proyecto = os.getenv("GCP_PROJECT_ID", "")
    return Config(
        modo=modo,
        proyecto=proyecto,
        region=os.getenv("GCP_REGION", "us-central1"),
        # Los modelos Gemini 3.x se sirven desde el endpoint "global".
        region_modelos=os.getenv("GCP_REGION_MODELOS", "global"),
        region_embeddings=os.getenv("GCP_REGION_EMBEDDINGS", "us-central1"),
        modelo=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        modelo_embeddings=os.getenv("EMBEDDING_MODEL", "gemini-embedding-001"),
        bucket=os.getenv("GCS_BUCKET", f"{proyecto}-migracion-sas" if proyecto else ""),
        dataset=os.getenv("BQ_DATASET", "migracion_sas"),
    )


config = cargar()
