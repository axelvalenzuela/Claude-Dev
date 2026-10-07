"""04 · Salida estructurada con Pydantic: JSON validado a partir de texto libre.

Concepto: para integrar un LLM con sistemas necesitas datos con esquema fijo.
response_schema hace que el modelo devuelva JSON que cumple el modelo de Pydantic,
y response.parsed te entrega el objeto ya validado.

    python 04_gemini_structured_output.py
"""

from typing import Literal

from google.genai import types
from pydantic import BaseModel, Field

from common import MODEL, client


class Ticket(BaseModel):
    cliente: str
    ciudad: str
    producto: str
    severidad: Literal["baja", "media", "alta"]
    resumen: str = Field(description="máximo 15 palabras")


texto = "Hola, soy Ana de Mexicali. Desde ayer la app de pagos me da error 500 al pagar con tarjeta. Es urgente."

response = client.models.generate_content(
    model=MODEL,
    contents=f"Clasifica este ticket de soporte:\n{texto}",
    config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Ticket),
)

ticket: Ticket = response.parsed
print(ticket.model_dump_json(indent=2))
print("Severidad:", ticket.severidad)
