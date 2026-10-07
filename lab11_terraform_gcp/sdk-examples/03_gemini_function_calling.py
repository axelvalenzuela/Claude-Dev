"""03 · Function calling automático: el modelo usa tus funciones de Python.

Concepto clave de los agentes. Con google-genai basta pasar funciones con type hints y docstring:
el SDK genera el esquema, ejecuta la función cuando el modelo la pide y le devuelve el resultado.

    python 03_gemini_function_calling.py
"""

from google.genai import types

from common import MODEL, client


def precio_maquina(tipo: str) -> dict:
    """Devuelve el precio por hora en USD de un tipo de máquina de Compute Engine en us-central1."""
    precios = {"e2-micro": 0.0084, "e2-small": 0.0168, "e2-medium": 0.0335}
    print(f"  -> el modelo llamó precio_maquina(tipo={tipo!r})")
    return {"tipo": tipo, "usd_por_hora": precios.get(tipo, "desconocido")}


def convertir_moneda(usd: float) -> dict:
    """Convierte dólares a pesos mexicanos con un tipo de cambio fijo de 18.5."""
    print(f"  -> el modelo llamó convertir_moneda(usd={usd})")
    return {"mxn": round(usd * 18.5, 2)}


response = client.models.generate_content(
    model=MODEL,
    contents="¿Cuánto cuesta al mes (730 h) una e2-small, en pesos mexicanos?",
    config=types.GenerateContentConfig(tools=[precio_maquina, convertir_moneda]),
)

print("\nRespuesta final:", response.text)
print("Llamadas registradas:", len(response.automatic_function_calling_history or []), "turnos")
