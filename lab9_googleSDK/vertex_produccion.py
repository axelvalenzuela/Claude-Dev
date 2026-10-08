"""
Lab 9 - Conceptos de Vertex AI para produccion

    1. Autenticacion con ADC/IAM (sin API keys) y region del endpoint.
    2. Reintentos con backoff exponencial y timeout (errores 429 de cuota y 5xx).
    3. labels: etiquetas que aparecen en la factura de GCP para saber que equipo/app gasto.
    4. Manejo de errores del SDK (google.genai.errors).

Los puntos 1 y 3 solo aplican con GOOGLE_GENAI_USE_VERTEXAI=true; el resto funciona en ambos.
"""

from google.genai import errors, types

from comun import MODELO, USA_VERTEX, backend, crear_cliente, imprimir_uso

# --- 2. Reintentos y timeout a nivel cliente ---
# 429 = RESOURCE_EXHAUSTED (cuota / tokens por minuto), 500/503 = errores temporales.
opciones_http = types.HttpOptions(
    timeout=60_000,  # milisegundos
    retry_options=types.HttpRetryOptions(
        attempts=4,
        initial_delay=1.0,
        max_delay=20.0,
        exp_base=2.0,
        http_status_codes=[429, 500, 503],
    ),
)
client = crear_cliente(http_options=opciones_http)
print(f"Backend: {backend()} | modelo: {MODELO}")

# --- 3. labels para atribuir costos (solo Vertex AI) ---
config = types.GenerateContentConfig(
    temperature=0.2,
    max_output_tokens=512,
    thinking_config=types.ThinkingConfig(thinking_budget=0),
)
if USA_VERTEX:
    config.labels = {"equipo": "ia-engineering", "app": "lab9", "ambiente": "dev"}
    print("labels:", config.labels, "-> filtrables en Facturacion > Informes por etiqueta")

# --- 4. Manejo de errores ---
try:
    response = client.models.generate_content(
        model=MODELO,
        contents="List 3 Vertex AI features that matter when moving a GenAI prototype to production.",
        config=config,
    )
    print(response.text)
    imprimir_uso(response)
except errors.ClientError as e:  # 4xx: tu peticion esta mal (permisos, cuota, modelo inexistente)
    if e.code == 429:
        print("Cuota agotada incluso tras los reintentos. Pide mas cuota o usa Provisioned Throughput.")
    elif e.code in (401, 403):
        print("Sin permisos. En Vertex AI la cuenta necesita el rol roles/aiplatform.user.")
    else:
        print(f"Error del cliente {e.code}: {e.message}")
except errors.ServerError as e:  # 5xx: problema del servicio, ya se reintento
    print(f"Error del servicio {e.code}: {e.message}")
