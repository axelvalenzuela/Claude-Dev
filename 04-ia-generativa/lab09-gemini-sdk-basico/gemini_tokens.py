"""Conteo de tokens de entrada y salida con el SDK de Google Gemini."""
from google import genai
import os
os.environ['GEMINI_API_KEY'] = "key_exmaple"
# El cliente lee la API key automáticamente desde GEMINI_API_KEY
client = genai.Client()
prompt = "Tell me about Marvel"

# Cuenta los tokens del prompt antes de enviarlo
input_tokens_count = client.models.count_tokens(
    model="gemini-2.5-flash", contents=prompt
)
print("total input tokens:", input_tokens_count.total_tokens)

# Genera la respuesta del modelo con el mismo prompt
response = client.models.generate_content(
    model="gemini-2.5-flash", contents=prompt
)
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
print("\n total output tokens:", response.usage_metadata.total_token_count)
print("\n Candidate token count:", response.usage_metadata.candidates_token_count)
print("\n Thought tokens count:", response.usage_metadata.thought_token_count)
print("\n Input tokens count:", response.usage_metadata.input_token_count)
