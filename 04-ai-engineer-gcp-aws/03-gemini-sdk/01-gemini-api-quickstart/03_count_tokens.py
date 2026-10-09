"""03 · Tokens: contar ANTES de llamar (count_tokens) y medir DESPUÉS (usage_metadata).

Los tokens son la unidad de costo y de límite de contexto. Entrada y salida tienen precios
distintos, y los tokens de razonamiento (thinking) se cobran como salida.

Correr:  python 03_count_tokens.py
"""
import os

from google import genai

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
client = genai.Client()
prompt = "Resume en 2 líneas qué es RAG."

# PASO 1: estimar antes de enviar (sirve para validar que cabe y para presupuestar).
estimado = client.models.count_tokens(model=MODEL, contents=prompt)
print("Tokens del prompt (estimado):", estimado.total_tokens)

# PASO 2: llamar y leer el desglose real que se cobró.
response = client.models.generate_content(model=MODEL, contents=prompt)
uso = response.usage_metadata
print(response.text)
print("\nprompt_token_count     (entrada):        ", uso.prompt_token_count)
print("candidates_token_count (salida visible): ", uso.candidates_token_count)
print("thoughts_token_count   (razonamiento):   ", uso.thoughts_token_count)   # None si no hubo thinking
print("total_token_count      (todo):           ", uso.total_token_count)
