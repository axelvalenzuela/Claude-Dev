"""Conteo de tokens de entrada y salida con el SDK de Google Gemini."""

from comun import MODELO, USA_VERTEX, crear_cliente

client = crear_cliente()
prompt = "Tell me about Marvel"

# Cuenta los tokens del prompt ANTES de enviarlo (no genera nada, no cuesta salida).
input_tokens_count = client.models.count_tokens(model=MODELO, contents=prompt)
print("total input tokens:", input_tokens_count.total_tokens)

# Solo Vertex AI: compute_tokens devuelve además los tokens uno por uno (útil para depurar prompts).
if USA_VERTEX:
    detalle = client.models.compute_tokens(model=MODELO, contents=prompt)
    for info in detalle.tokens_info:
        print("tokens:", [t.decode("utf-8", errors="replace") for t in info.tokens])

# Genera la respuesta del modelo con el mismo prompt
response = client.models.generate_content(model=MODELO, contents=prompt)
print(response.text)

# usage_metadata trae el desglose real de tokens que se cobraron en la llamada.
# Sirve para medir costo y vigilar límites: entrada y salida tienen precios distintos.
#   prompt_token_count     -> tokens del prompt (entrada). Debe coincidir con count_tokens;
#                             la diferencia es que count_tokens lo calcula ANTES de enviar
#                             (útil para validar que el prompt cabe o estimar costo).
#   candidates_token_count -> tokens del texto que respondió el modelo (salida visible).
#   thoughts_token_count   -> tokens que el modelo usó para "pensar" antes de responder.
#                             No aparecen en response.text, pero sí se cobran como salida.
#   total_token_count      -> suma de todo: entrada + salida + razonamiento.
uso = response.usage_metadata
print("\n total tokens:", uso.total_token_count)
print("\n Candidate token count:", uso.candidates_token_count)
print("\n Thought tokens count:", uso.thoughts_token_count)
print("\n Input tokens count:", uso.prompt_token_count)
