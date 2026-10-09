"""Ejercicio 10 — ¿Está todo listo para hablar con GCP?

Revisa, en orden, cada cosa que suele fallar la primera vez y te dice cómo
arreglarla. Córrelo SIEMPRE que algo no funcione: el 80 % de los errores
de los labs siguientes son de este checklist.

Correr (desde 04-vertex-ai-projects/):   python 10_setup_gcp/verificar_entorno.py
"""
import importlib.util
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # para importar comun/
from comun.config import RAIZ, config  # noqa: E402

OK, FALLA, AVISO = "[ OK ]", "[FALLA]", "[AVISO]"
hubo_falla = False


def reportar(estado, mensaje, arreglo=""):
    global hubo_falla
    hubo_falla |= estado == FALLA
    print(f"{estado} {mensaje}")
    if arreglo and estado != OK:
        print(f"        -> {arreglo}")


def main():
    print(f"Modo: {config.modo.upper()}\n")

    # PASO #1: Python y librerías
    version = sys.version_info
    reportar(OK if version >= (3, 10) else FALLA, f"Python {version.major}.{version.minor}",
             "Instala Python 3.10+ (o usa: uv run --python 3.12 ...)")
    for paquete, modulo in [("google-genai", "google.genai"), ("pydantic", "pydantic"), ("pandas", "pandas"),
                            ("python-dotenv", "dotenv"), ("google-cloud-bigquery", "google.cloud.bigquery")]:
        reportar(OK if _existe(modulo) else FALLA, f"paquete {paquete}", "pip install -r requirements.txt")

    # PASO #2: archivo .env
    reportar(OK if (RAIZ / ".env").exists() else AVISO, "archivo 04-vertex-ai-projects/.env",
             "cp .env.example .env   (sin .env todo corre en modo simulado)")

    if not config.es_real:
        print("\nEn modo simulado no hace falta nada más. Para conectar GCP sigue docs/gcp-connect.md")
        print("y pon MODO=real en .env; luego vuelve a correr este script.")
        return

    # PASO #3: proyecto y herramientas de GCP
    proyecto_ok = config.proyecto and config.proyecto != "tu-proyecto-gcp"
    reportar(OK if proyecto_ok else FALLA, f"GCP_PROJECT_ID = {config.proyecto or '(vacío)'}",
             "Pon tu ID real: gcloud config get-value project")
    reportar(OK if shutil.which("gcloud") else AVISO, "gcloud CLI instalado",
             "https://cloud.google.com/sdk/docs/install (lo necesitas para login y deploy)")

    # PASO #4: credenciales (ADC = Application Default Credentials)
    try:
        import google.auth

        credenciales, proyecto_adc = google.auth.default()
        reportar(OK, f"credenciales ADC encontradas (proyecto por defecto: {proyecto_adc})")
    except Exception as e:  # noqa: BLE001 - queremos mostrar cualquier problema de auth
        reportar(FALLA, f"sin credenciales: {type(e).__name__}", "gcloud auth application-default login")
        return

    # PASO #5: una llamada real y barata a Gemini y a embeddings
    from comun import llm

    try:
        r = llm.generar("Responde solamente con la palabra: LISTO", rol="verificacion")
        reportar(OK, f"Gemini ({config.modelo}) respondió: {r.texto.strip()[:40]!r} "
                     f"[{r.tokens_entrada}+{r.tokens_salida} tokens, ${r.costo_usd:.6f}]")
    except Exception as e:  # noqa: BLE001
        reportar(FALLA, f"Gemini falló: {e}", _pista(str(e)))
    try:
        v = llm.embeber(["hola"])[0]
        reportar(OK, f"Embeddings ({config.modelo_embeddings}) -> vector de {len(v)} números")
    except Exception as e:  # noqa: BLE001
        reportar(FALLA, f"Embeddings fallaron: {e}", _pista(str(e)))

    print("\nTodo listo." if not hubo_falla else "\nArregla los [FALLA] de arriba y vuelve a correr.")


def _existe(modulo):
    try:
        return importlib.util.find_spec(modulo) is not None
    except ModuleNotFoundError:
        return False


def _pista(error: str) -> str:
    if "403" in error or "PERMISSION_DENIED" in error:
        return ("¿Habilitaste la API? gcloud services enable aiplatform.googleapis.com  "
                "| ¿Tu usuario tiene rol 'Vertex AI User'?")
    if "404" in error or "NOT_FOUND" in error:
        return "El modelo no existe en esa región: cambia GEMINI_MODEL o GCP_REGION_MODELOS en .env"
    if "429" in error or "RESOURCE_EXHAUSTED" in error:
        return "Cuota agotada: espera un minuto o pide más cuota en IAM y administración > Cuotas"
    if "billing" in error.lower():
        return "El proyecto no tiene facturación ligada: gcloud billing projects link ..."
    return "Revisa la tabla de errores en 10_setup_gcp/INSTRUCCIONES.md"


if __name__ == "__main__":
    main()
    sys.exit(1 if hubo_falla else 0)
