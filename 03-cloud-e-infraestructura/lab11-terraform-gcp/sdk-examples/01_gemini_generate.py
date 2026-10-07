"""01 · Primera llamada a Gemini en Vertex AI con el SDK google-genai.

Concepto: el mismo SDK sirve para la Gemini API (con API key) y para Vertex AI (vertexai=True,
con IAM y datos dentro de tu proyecto). En empresas se usa Vertex AI.
Observa: texto, finish_reason y los tokens de entrada/salida (lo que pagas).

    python 01_gemini_generate.py
"""

from google.genai import types

from common import MODEL, client

response = client.models.generate_content(
    model=MODEL,
    contents="¿Qué es una función serverless?",
    config=types.GenerateContentConfig(
        system_instruction="Eres un tutor de cloud. Responde en español en máximo 3 líneas.",
        max_output_tokens=200,
        temperature=0.3,
    ),
)

print("Respuesta:", response.text)
print("finish_reason:", response.candidates[0].finish_reason)     # STOP | MAX_TOKENS | SAFETY ...
usage = response.usage_metadata
print(f"Tokens: entrada={usage.prompt_token_count} salida={usage.candidates_token_count} total={usage.total_token_count}")
