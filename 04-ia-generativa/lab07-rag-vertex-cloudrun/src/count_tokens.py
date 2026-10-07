"""CLI: cuenta tokens para Gemini y muestra el uso real que reporta la API.

Dos mediciones distintas, a propósito:
  1. Conteo PREVIO a llamar al modelo (`client.models.count_tokens`, vía
     src/gemini_client.py:count_tokens) — no gasta cuota ni dinero, sirve
     para presupuestar un prompt antes de enviarlo.
  2. `usage_metadata` de una llamada real a `generate_content` (vía
     src/gemini_client.py:generate_answer_with_usage) — lo que Vertex AI
     realmente facturó: tokens de entrada, de salida y el total.

Uso:
    python -m src.count_tokens "cual es el objetivo del programa Helios?"
    python -m src.count_tokens          # usa una pregunta de ejemplo
"""
from __future__ import annotations

import sys

from src.gemini_client import count_tokens, generate_answer_with_usage

DEFAULT_QUESTION = "En una frase, que es un sistema RAG?"


def main() -> None:
    question = " ".join(sys.argv[1:]).strip() or DEFAULT_QUESTION

    print(f"Pregunta: {question!r}")

    pre_count = count_tokens(question)
    print(f"Tokens de entrada (conteo previo, sin llamar al modelo): {pre_count}")

    print("\nLlamando a Gemini (generate_content)...")
    answer, usage = generate_answer_with_usage(question)

    print(f"\nRespuesta: {answer}")

    print("\nUso real reportado por la API (response.usage_metadata):")
    print(f"  prompt_token_count:         {usage.prompt_token_count}")
    print(f"  candidates_token_count:     {usage.candidates_token_count}")

    # gemini-2.5-* factura tokens de "thinking" aparte; otros modelos no
    # tienen este campo, por eso se imprime solo si el SDK lo trae.
    thoughts = getattr(usage, "thoughts_token_count", None)
    if thoughts is not None:
        print(f"  thoughts_token_count:       {thoughts}")

    cached = getattr(usage, "cached_content_token_count", None)
    if cached is not None:
        print(f"  cached_content_token_count: {cached}")

    print(f"  total_token_count:          {usage.total_token_count}")


if __name__ == "__main__":
    main()
