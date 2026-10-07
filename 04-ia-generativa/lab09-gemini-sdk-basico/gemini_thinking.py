from google import genai
from google.genai import types
import os
os.environ['GEMINI_API_KEY'] = "key_exmaple"
client = genai.Client()
prompt = "Tell me about Marvel"

# thinking_budget = cuántos tokens máximo puede usar el modelo para "pensar" antes de responder.
#   0          -> thinking apagado. Respuesta más rápida y barata, por eso
#                 thoughts_token_count sale None (no hubo razonamiento que contar).
#   -1         -> dinámico (default): el modelo decide cuánto pensar según la dificultad.
#   1 a 24576  -> límite fijo (gemini-2.5-flash). Es un TOPE, no una meta: en prompts
#                 simples puede usar menos. Más budget = mejor razonamiento en tareas
#                 complejas, pero más latencia y costo (los thoughts se cobran como salida).
# Nota: gemini-2.5-pro no permite apagarlo (mínimo 128).
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0) #disable thinkin LLM
        ),
    maxOutputTokens=300,    
)

# usage_metadata: desglose de tokens cobrados en la llamada.
#   prompt_token_count     -> entrada (el prompt).
#   candidates_token_count -> salida visible (response.text).
#   thoughts_token_count   -> razonamiento interno; None si thinking_budget=0.
#   total_token_count      -> entrada + salida + razonamiento.
print("\n Total tokens:", response.usage_metadata.total_token_count)
print("\n Candidate token count:", response.usage_metadata.candidates_token_count)
print("\n Thought tokens count:", response.usage_metadata.thoughts_token_count)
print("\n Input tokens count:", response.usage_metadata.prompt_token_count)
