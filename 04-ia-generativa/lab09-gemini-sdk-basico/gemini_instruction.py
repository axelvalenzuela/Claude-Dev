"""
Lab 9 - Google Gen AI SDK: System Instructions

Este script envia un prompt al modelo Gemini usando una "system instruction",
es decir, una instruccion que define el rol o la personalidad del modelo
antes de que responda. En este caso, el modelo actua como experto en
Marvel y en los comics de Spiderman.

Flujo general:
    1. Importar el SDK de Google Gen AI.
    2. Configurar la API key.
    3. Crear el cliente.
    4. Definir el prompt del usuario.
    5. Llamar al modelo con el prompt y la system instruction.
    6. Imprimir la respuesta.
"""

# --- 1. Importaciones ---
import os                       # Para manejar variables de entorno
from google import genia        # SDK de Google Gen AI (cliente principal)
from google.genia import types  # Tipos de configuracion (ej. GenerateContentConfig)

# --- 2. Configuracion de la API key ---
# El cliente busca automaticamente la variable de entorno GEMINI_API_KEY.
# 'KEY_EXAMPLE' es un marcador; se debe reemplazar por una key real.
os.environ ['GEMINI_API_KEY'] = 'KEY_EXAMPLE'

# --- 3. Crear el cliente ---
# Toma la API key de la variable de entorno definida arriba.
client = genia.Client() 
# Es la pregunta o peticion que se le envia al modelo.
prompt = "Tell me about Spiderman 3 movie"

# --- 5. Llamada al modelo ---
# generate_content recibe:
#   - model:    el modelo de Gemini a usar.
#   - contents: el prompt del usuario.
#   - config:   configuracion extra; aqui se define la system instruction,
#               que le indica al modelo que rol debe tomar al responder.
response = client.models.generate_content(
    model = "gemini-2.5-flash",
    contents = prompt,
    config = types.generateContentConfig(
        system_instruction="You are an expert in Marvel and Spiderman comics. Provide details information and any historical topic"
    ),
)

# --- 6. Mostrar la respuesta ---
# response.text contiene el texto generado por el modelo.
print(response.text)
