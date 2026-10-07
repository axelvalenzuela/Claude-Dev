"""02 · Streaming: mostrar la respuesta mientras se genera.

Concepto: en un chat el usuario percibe velocidad por el "time to first token",
no por el tiempo total. converse_stream entrega eventos con fragmentos de texto.

    python 02_bedrock_streaming.py
"""

import time

from common import MODEL, bedrock

start = time.perf_counter()
first_token = None

stream = bedrock.converse_stream(
    modelId=MODEL,
    messages=[{"role": "user", "content": [{"text": "Explica en 5 viñetas qué es Terraform."}]}],
    inferenceConfig={"maxTokens": 300},
)

for event in stream["stream"]:
    if "contentBlockDelta" in event:
        if first_token is None:
            first_token = time.perf_counter() - start
        print(event["contentBlockDelta"]["delta"]["text"], end="", flush=True)
    elif "metadata" in event:
        usage = event["metadata"]["usage"]

print(f"\n\nPrimer token: {first_token:.2f} s · total: {time.perf_counter() - start:.2f} s · tokens: {usage}")
