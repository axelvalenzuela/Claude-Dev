"""01 · La llamada mínima a Gemini: cliente + generate_content.

Requisitos:  pip install -r requirements.txt  y  export GEMINI_API_KEY=<tu-key>
Correr:      python 01_generate.py "¿Qué es un embedding?"
"""
import os
import sys

from google import genai

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# PASO 1: el cliente lee GEMINI_API_KEY del entorno. Nunca escribas la key en el código.
client = genai.Client()

# PASO 2: una sola llamada. contents puede ser un string, una lista de partes o un historial.
prompt = sys.argv[1] if len(sys.argv) > 1 else "Explica en 3 líneas qué es un LLM."
response = client.models.generate_content(model=MODEL, contents=prompt)

# PASO 3: response.text junta el texto del primer candidato.
print(response.text)
