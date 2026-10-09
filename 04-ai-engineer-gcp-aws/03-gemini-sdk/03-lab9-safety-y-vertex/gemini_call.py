"""Lab 9 - Primera llamada a Gemini (la mas simple posible)."""

from comun import MODELO, backend, crear_cliente

# La API key ya no se escribe aqui: crear_cliente() la lee del archivo .env.
client = crear_cliente()

response = client.models.generate_content(
    model=MODELO,
    contents="Tell me about Marvel",
)

print(f"[{backend()} | {MODELO}]\n")
print(response.text)
