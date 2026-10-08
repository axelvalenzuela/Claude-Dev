"""
Lab 9 - Parametros de generacion: temperature, top_p, top_k, seed, stop_sequences, max_output_tokens.

    temperature  0.0 - 2.0  -> aleatoriedad. 0 = casi determinista (extraccion, clasificacion);
                               alto = mas creativo (lluvia de ideas, marketing).
    top_p        0.0 - 1.0  -> solo considera los tokens que suman esa probabilidad (nucleus sampling).
    top_k        entero     -> solo considera los k tokens mas probables.
    seed         entero     -> con la misma seed y mismos parametros, respuestas reproducibles (best effort).
    stop_sequences          -> el modelo se detiene al generar alguno de estos textos.
    max_output_tokens       -> tope de salida. Si se alcanza, finish_reason = MAX_TOKENS.
"""

from google.genai import types

from comun import MODELO, crear_cliente

client = crear_cliente()
prompt = "Give me a creative name for a coffee shop run by Spiderman. Only the name."


def generar(titulo: str, **parametros) -> None:
    response = client.models.generate_content(
        model=MODELO,
        contents=prompt,
        config=types.GenerateContentConfig(
            # Thinking apagado: así max_output_tokens solo cuenta la respuesta visible.
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            **parametros,
        ),
    )
    candidato = response.candidates[0]
    print(f"{titulo:45} -> {(response.text or '').strip()!r}  [finish_reason={candidato.finish_reason.name}]")


print("--- temperature baja: casi siempre la misma respuesta ---")
for _ in range(3):
    generar("temperature=0", temperature=0)

print("\n--- temperature alta + top_p/top_k: mas variedad ---")
for _ in range(3):
    generar("temperature=1.5, top_p=0.95, top_k=40", temperature=1.5, top_p=0.95, top_k=40)

print("\n--- seed: misma seed = misma respuesta aun con temperature alta ---")
for _ in range(2):
    generar("temperature=1.5, seed=42", temperature=1.5, seed=42)

print("\n--- stop_sequences y max_output_tokens ---")
generar('stop_sequences=["Caf", "Web"]', stop_sequences=["Caf", "Web"])
generar("max_output_tokens=3", max_output_tokens=3)
