"""18 · Safety settings: umbrales por categoría y cómo detectar un bloqueo.

Concepto: Gemini evalúa entrada y salida por categorías (odio, acoso, sexual, peligroso).
Cada categoría tiene un umbral configurable; si se bloquea, finish_reason = SAFETY
y safety_ratings explica por qué. Para defensa completa combina con Model Armor (micro lab 15).

    python 18_safety_settings.py
"""

from google.genai import types

from common import MODEL, client

strict = [types.SafetySetting(category=c, threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE) for c in (
    types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
    types.HarmCategory.HARM_CATEGORY_HARASSMENT,
    types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
    types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
)]

for prompt in ["Dame 3 consejos para una entrevista técnica.",
               "Escribe un insulto muy ofensivo para mi compañero de trabajo."]:
    response = client.models.generate_content(
        model=MODEL, contents=prompt, config=types.GenerateContentConfig(safety_settings=strict))
    candidate = response.candidates[0] if response.candidates else None
    print(f"> {prompt}")
    print("  finish_reason:", candidate.finish_reason if candidate else response.prompt_feedback)
    if candidate and candidate.safety_ratings:
        flagged = [(r.category.name, r.probability.name) for r in candidate.safety_ratings if r.probability.name != "NEGLIGIBLE"]
        print("  categorías con riesgo:", flagged or "ninguna")
    print("  texto:", (response.text or "(bloqueado)")[:120], "\n")
