"""
Lab 9 - Salida estructurada (JSON con esquema)

En vez de pedir "responde en JSON" y rezar, se le da al modelo un esquema (Pydantic).
Gemini garantiza que la respuesta cumple el esquema y el SDK la convierte en objeto:
response.parsed. Es la base para extraer datos de documentos (facturas, contratos, correos).
"""

from enum import Enum

from google.genai import types
from pydantic import BaseModel, Field

from comun import MODELO, crear_cliente


class Categoria(str, Enum):
    viaticos = "viaticos"
    software = "software"
    oficina = "oficina"
    otros = "otros"


class Gasto(BaseModel):
    concepto: str
    monto: float = Field(description="Monto sin IVA en pesos mexicanos")
    categoria: Categoria
    deducible: bool


class ReporteGastos(BaseModel):
    gastos: list[Gasto]
    total: float


client = crear_cliente()

correo = """
Hola, te paso mis gastos del viaje a Monterrey: el vuelo costó 3,450 pesos y el hotel 2 noches
fueron 2,800. También pagué la licencia anual de Office por 1,999 y unas plumas y libretas por 230.
Ah, y una comida con un cliente de 1,150 (sin factura).
"""

response = client.models.generate_content(
    model=MODELO,
    contents=f"Extrae los gastos de este correo:\n{correo}",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ReporteGastos,
        temperature=0,  # extraccion = queremos la respuesta mas estable
        system_instruction="Un gasto es deducible solo si tiene factura.",
    ),
)

reporte: ReporteGastos = response.parsed  # ya es un objeto de Pydantic, no texto
for g in reporte.gastos:
    print(f"{g.concepto:35} ${g.monto:>10,.2f}  {g.categoria.value:10} deducible={g.deducible}")
print(f"{'TOTAL':35} ${reporte.total:>10,.2f}")
print("\nJSON crudo:", response.text)
