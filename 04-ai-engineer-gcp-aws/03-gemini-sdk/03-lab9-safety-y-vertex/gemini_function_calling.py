"""
Lab 9 - Function calling (herramientas)

El modelo no puede consultar tus sistemas por si solo, pero puede PEDIR que ejecutes una
funcion. Con el SDK de Python basta pasar funciones normales en tools=[...]:
    - Modo automatico (default): el SDK ejecuta la funcion y le regresa el resultado al modelo.
    - Modo manual: el modelo solo propone la llamada (response.function_calls) y tu decides.
El docstring y los type hints de la funcion son la "descripcion" que lee el modelo.
"""

from google.genai import types

from comun import MODELO, crear_cliente


def tipo_de_cambio(moneda: str) -> dict:
    """Devuelve cuantos pesos mexicanos vale 1 unidad de la moneda (USD, EUR o JPY)."""
    tabla = {"USD": 18.45, "EUR": 20.10, "JPY": 0.125}  # datos simulados para el lab
    return {"moneda": moneda.upper(), "mxn": tabla.get(moneda.upper(), "desconocida")}


def calcular_iva(monto: float, tasa: float) -> dict:
    """Calcula el IVA de un monto. tasa es una fraccion, por ejemplo 0.16 para 16%."""
    iva = round(monto * tasa, 2)
    return {"subtotal": monto, "iva": iva, "total": round(monto + iva, 2)}


client = crear_cliente()
pregunta = "Compré un software de 250 dólares. ¿Cuánto es en pesos y cuánto sería con IVA del 16%?"

# --- Modo automatico ---
response = client.models.generate_content(
    model=MODELO,
    contents=pregunta,
    config=types.GenerateContentConfig(tools=[tipo_de_cambio, calcular_iva], temperature=0),
)
print("Respuesta final:\n", response.text)

print("\nLlamadas que hizo el modelo:")
for contenido in response.automatic_function_calling_history or []:
    for part in contenido.parts or []:
        if part.function_call:
            print(f"  -> {part.function_call.name}({dict(part.function_call.args)})")
        if part.function_response:
            print(f"  <- {part.function_response.response}")

# --- Modo manual: util cuando la funcion tiene efectos (pagos, correos) y requiere aprobacion ---
response = client.models.generate_content(
    model=MODELO,
    contents="¿Cuántos pesos son 1000 euros?",
    config=types.GenerateContentConfig(
        tools=[tipo_de_cambio],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    ),
)
print("\nModo manual, el modelo propone:")
for llamada in response.function_calls or []:
    print(f"  {llamada.name}({dict(llamada.args)})  <- tu codigo decide si ejecutarla")
