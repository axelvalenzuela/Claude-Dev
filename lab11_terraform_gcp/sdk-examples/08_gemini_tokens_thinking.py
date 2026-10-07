"""08 · Tokens, razonamiento (thinking) y costo antes de llamar al modelo.

Concepto: count_tokens estima el costo ANTES de enviar. Los modelos 2.5 "piensan" antes de
responder y esos thinking tokens también se cobran: thinking_budget los limita (0 = sin pensar).

    python 08_gemini_tokens_thinking.py
"""

from google.genai import types

from common import MODEL, client

prompt = "Un tren sale a las 9:40 y tarda 2 h 35 min. Hace una escala de 25 min. ¿A qué hora llega?"

print("Tokens estimados del prompt:", client.models.count_tokens(model=MODEL, contents=prompt).total_tokens)

for budget in (0, 1024):
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=budget)),
    )
    u = response.usage_metadata
    print(f"\nthinking_budget={budget}: {response.text.strip()[:120]}")
    print(f"  entrada={u.prompt_token_count} pensamiento={u.thoughts_token_count or 0} salida={u.candidates_token_count}")
