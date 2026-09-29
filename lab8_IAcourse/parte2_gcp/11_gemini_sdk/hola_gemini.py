"""Micro lab 11 — Tu primera llamada a Gemini con el SDK google-genai.

Tres llamadas, cada una agrega UNA idea:
  PASO 1: prompt simple                    -> texto
  PASO 2: + instrucción de sistema          -> controlas rol, tono y formato
  PASO 3: leer tokens, costo y latencia     -> lo que te preguntan en producción

El código que habla con Vertex está en comun/llm.py (función generar). Léelo
después de correr esto: son ~30 líneas.

Correr (desde parte2_gcp/):   python 11_gemini_sdk/hola_gemini.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comun import llm  # noqa: E402
from comun.config import config  # noqa: E402

SAS_EJEMPLO = (Path(__file__).resolve().parents[1] / "comun" / "sas" / "ventas.sas").read_text(encoding="utf-8")


def main():
    print(f"Modo {config.modo} | modelo {config.modelo}\n")

    # PASO 1 — prompt simple
    r = llm.generar("En 3 oraciones: ¿qué implica migrar SAS a Python en Google Cloud?")
    print("PASO 1 — prompt simple\n", r.texto, "\n")

    # PASO 2 — instrucción de sistema: define QUIÉN es el modelo y sus reglas.
    # Va separada del prompt del usuario y pesa más que él.
    sistema = (
        "Eres un ingeniero senior de migración SAS->Python. Respondes en español, "
        "en viñetas, máximo 5 viñetas, sin introducción."
    )
    r = llm.generar(f"Explica qué hace este programa SAS:\n\n{SAS_EJEMPLO}", sistema=sistema)
    print("PASO 2 — con instrucción de sistema\n", r.texto, "\n")

    # PASO 3 — métricas de la llamada (vienen en response.usage_metadata)
    print("PASO 3 — métricas de la última llamada")
    print(f"  tokens de entrada: {r.tokens_entrada}")
    print(f"  tokens de salida:  {r.tokens_salida}   (incluye 'thinking tokens')")
    print(f"  latencia:          {r.latencia_s} s")
    print(f"  costo estimado:    ${r.costo_usd:.6f} USD")
    print(f"  -> 1,000 programas así costarían ~${r.costo_usd * 1000:.2f} USD")
    if not config.es_real:
        print("\n(Modo simulado: tokens aproximados y costo de lo que HABRÍA costado.)")


if __name__ == "__main__":
    main()
