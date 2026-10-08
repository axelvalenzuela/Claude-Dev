"""
Lab 9 - Configuracion compartida por todos los scripts.

Crea el cliente del SDK google-genai para cualquiera de los dos "backends":
    - Gemini Developer API -> se autentica con API key (GEMINI_API_KEY). Ideal para prototipos.
    - Vertex AI            -> se autentica con IAM / ADC (gcloud auth application-default login)
                              y usa un proyecto y una region de GCP. Es lo que se usa en empresa.

El mismo codigo funciona en ambos: solo cambian las variables de entorno del archivo .env
(ver .env.example). Por eso la API key NUNCA se escribe dentro del codigo.
"""

import os

from google import genai
from google.genai import types

# python-dotenv carga las variables del archivo .env (si esta instalado).
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

MODELO = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MODELO_EMBEDDINGS = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
USA_VERTEX = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").strip().lower() in {"1", "true", "yes", "si"}


def crear_cliente(http_options: types.HttpOptions | None = None) -> genai.Client:
    """Devuelve un cliente listo para Gemini API o Vertex AI segun el .env."""
    if USA_VERTEX:
        proyecto = os.getenv("GOOGLE_CLOUD_PROJECT")
        region = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        if not proyecto:
            raise SystemExit("Falta GOOGLE_CLOUD_PROJECT en .env (modo Vertex AI).")
        # En Vertex AI no hay API key: se usan las credenciales de ADC (IAM).
        return genai.Client(vertexai=True, project=proyecto, location=region, http_options=http_options)

    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        raise SystemExit("Falta GEMINI_API_KEY. Copia .env.example a .env y pon tu key.")
    return genai.Client(http_options=http_options)


def backend() -> str:
    return "Vertex AI" if USA_VERTEX else "Gemini Developer API"


def imprimir_uso(response) -> None:
    """Imprime el desglose de tokens cobrados (usage_metadata)."""
    uso = response.usage_metadata
    if uso is None:
        print("\n[tokens] (sin usage_metadata)")
        return
    print(
        f"\n[tokens] entrada={uso.prompt_token_count} salida={uso.candidates_token_count} "
        f"razonamiento={uso.thoughts_token_count or 0} total={uso.total_token_count}"
    )
