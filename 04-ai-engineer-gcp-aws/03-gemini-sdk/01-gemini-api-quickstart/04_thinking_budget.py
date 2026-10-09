"""04 · Thinking budget: cuánto puede "pensar" el modelo antes de responder.

thinking_budget (Gemini 2.5):
    0         -> sin razonamiento: más rápido y barato (solo Flash/Flash-Lite; Pro exige >= 128)
    -1        -> dinámico: el modelo decide según la dificultad
    1..24576  -> tope fijo (Flash). Es un máximo, no una meta.
Más presupuesto = mejor razonamiento en problemas difíciles, pero más latencia y costo.

Correr:  python 04_thinking_budget.py
"""
import os
import time

from google import genai
from google.genai import types

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
client = genai.Client()
prompt = "Un tren sale a las 9:40 y tarda 2 h 35 min con una escala de 25 min. ¿A qué hora llega?"

# PASO 1: misma pregunta con tres presupuestos; compara tokens y latencia.
for budget in (0, 1024, -1):
    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=budget),
        max_output_tokens=300,   # va DENTRO de la config, en snake_case
    )
    inicio = time.perf_counter()
    response = client.models.generate_content(model=MODEL, contents=prompt, config=config)
    uso = response.usage_metadata
    print(f"\n===== thinking_budget={budget}  ({time.perf_counter() - inicio:.1f} s) =====")
    print(response.text)
    print(f"tokens -> salida: {uso.candidates_token_count}, razonamiento: {uso.thoughts_token_count}")
