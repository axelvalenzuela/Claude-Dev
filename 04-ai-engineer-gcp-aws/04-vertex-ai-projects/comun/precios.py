"""Precios aproximados por 1 millón de tokens, en USD (Vertex AI, sept. 2026).

Sirven para ESTIMAR el costo de cada llamada (también en modo simulado,
para que veas cuánto habría costado). Los precios cambian: confirma en
https://cloud.google.com/vertex-ai/generative-ai/pricing antes de decidir
nada con dinero real. Ver docs/gcp-costs.pdf.
"""

# modelo: (entrada, salida)   — la salida incluye los "thinking tokens"
PRECIOS_POR_MILLON = {
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-3-flash": (0.50, 3.00),
    "gemini-3.5-flash": (1.50, 9.00),
    "gemini-3.8-flash": (0.75, 3.75),   # precio introductorio hasta 31-dic-2026
    "gemini-3.1-pro": (2.00, 12.00),    # hasta 200K tokens de entrada
    "gemini-2.5-flash": (0.30, 2.50),   # se retira ~oct-2026
    "gemini-embedding-001": (0.15, 0.0),
    "text-embedding-005": (0.10, 0.0),
}


def costo_usd(modelo: str, tokens_entrada: int, tokens_salida: int) -> float:
    entrada, salida = PRECIOS_POR_MILLON.get(modelo, (0.0, 0.0))
    return (tokens_entrada * entrada + tokens_salida * salida) / 1_000_000
