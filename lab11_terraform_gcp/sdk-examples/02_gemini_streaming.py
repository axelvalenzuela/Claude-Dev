"""02 · Streaming: mostrar la respuesta mientras se genera.

Concepto: en un chat el usuario percibe velocidad por el "time to first token".
generate_content_stream entrega fragmentos (chunks) conforme el modelo los produce.

    python 02_gemini_streaming.py
"""

import time

from common import MODEL, client

start = time.perf_counter()
first_token = None

for chunk in client.models.generate_content_stream(model=MODEL, contents="Explica en 5 viñetas qué es Terraform."):
    if chunk.text:
        if first_token is None:
            first_token = time.perf_counter() - start
        print(chunk.text, end="", flush=True)
    usage = chunk.usage_metadata  # el último chunk trae el conteo final

print(f"\n\nPrimer token: {first_token:.2f} s · total: {time.perf_counter() - start:.2f} s · tokens: {usage.total_token_count}")
