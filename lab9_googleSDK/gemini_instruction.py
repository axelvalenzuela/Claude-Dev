"""
Lab 9 - Google Gen AI SDK: System Instructions

Este script envia un prompt al modelo Gemini usando una "system instruction",
es decir, una instruccion que define el rol o la personalidad del modelo
antes de que responda. En este caso, el modelo actua como experto en
Marvel y en los comics de Spiderman.

Flujo general:
    1. Importar el SDK de Google Gen AI.
    2. Crear el cliente (la API key / proyecto vienen del .env).
    3. Definir el prompt del usuario.
    4. Llamar al modelo con el prompt y la system instruction.
    5. Imprimir la respuesta.
"""

# --- 1. Importaciones ---
from google.genai import types  # Tipos de configuracion (ej. GenerateContentConfig)

from comun import MODELO, crear_cliente, imprimir_uso

# --- 2. Crear el cliente ---
# crear_cliente() lee GEMINI_API_KEY (o el proyecto de Vertex AI) del archivo .env.
client = crear_cliente()

# --- 3. Prompt del usuario ---
# Es la pregunta o peticion que se le envia al modelo.
prompt = "Tell me about Spiderman 3 movie"

# --- 4. Llamada al modelo ---
# generate_content recibe:
#   - model:    el modelo de Gemini a usar.
#   - contents: el prompt del usuario.
#   - config:   configuracion extra; aqui se define la system instruction,
#               que le indica al modelo que rol debe tomar al responder.
# La system instruction tambien es la primera linea de defensa de seguridad:
# limita el tema y el tono ANTES de que entren los safety settings (ver gemini_safety.py).
response = client.models.generate_content(
    model=MODELO,
    contents=prompt,
    config=types.GenerateContentConfig(
        system_instruction=(
            "You are an expert in Marvel and Spiderman comics. "
            "Provide detailed information and any historical context. "
            "If the question is not about Marvel, politely say it is out of scope."
        ),
    ),
)

# --- 5. Mostrar la respuesta ---
# response.text contiene el texto generado por el modelo.
print(response.text)
imprimir_uso(response)
