"""16 · Producción: llamadas concurrentes con límite y reintentos con backoff.

Concepto: las APIs de modelos tienen cuotas (RPM/TPM). En producción se limita la concurrencia
(semáforo) y se reintentan los errores 429/503 con backoff exponencial + jitter.

    python 16_async_concurrencia_reintentos.py
"""

import asyncio
import random
import time

from google.genai import errors

from common import MODEL, client

MAX_CONCURRENT = 4
semaphore = asyncio.Semaphore(MAX_CONCURRENT)


async def classify(text, attempts=5):
    async with semaphore:
        for attempt in range(attempts):
            try:
                response = await client.aio.models.generate_content(
                    model=MODEL, contents=f"Sentimiento (positivo/negativo/neutral) de: {text}. Una palabra.")
                return text, response.text.strip()
            except errors.APIError as error:
                if error.code not in (429, 500, 503) or attempt == attempts - 1:
                    raise
                wait = (2 ** attempt) + random.random()          # backoff exponencial + jitter
                print(f"  {error.code} en '{text[:20]}', reintento en {wait:.1f}s")
                await asyncio.sleep(wait)


async def main():
    texts = [f"Comentario {i}: el servicio {'funcionó perfecto' if i % 2 else 'se cayó otra vez'}" for i in range(12)]
    start = time.perf_counter()
    results = await asyncio.gather(*(classify(t) for t in texts))
    for text, label in results:
        print(f"{label:10} <- {text}")
    print(f"\n{len(texts)} llamadas en {time.perf_counter() - start:.1f}s con máximo {MAX_CONCURRENT} simultáneas")


asyncio.run(main())
