"""Micro lab 08 — Temperatura: qué tan "creativo" o "predecible" es el modelo.

Antes de escoger el siguiente token, el modelo produce un PUNTAJE (logit)
para cada candidato. La función SOFTMAX convierte esos puntajes en
probabilidades que suman 100%. La TEMPERATURA divide los puntajes antes:

    temperatura baja  (0.2) -> el favorito se lleva casi todo: predecible
    temperatura 1.0         -> las probabilidades "naturales" del modelo
    temperatura alta  (2.0) -> todo se empareja: variado, y a veces absurdo

Correr:  python temperatura.py
"""
import math
import random
from collections import Counter

random.seed(1)

PROMPT = "El cielo hoy está..."
# Puntajes inventados que un modelo podría dar a cada siguiente palabra.
LOGITS = {"azul": 4.0, "nublado": 3.2, "despejado": 3.0, "gris": 2.5, "morado": 0.5, "delicioso": -1.0}


def softmax(logits, temperatura):
    escalados = {t: v / temperatura for t, v in logits.items()}
    maximo = max(escalados.values())               # restar el máximo evita overflow
    exps = {t: math.exp(v - maximo) for t, v in escalados.items()}
    total = sum(exps.values())
    return {t: e / total for t, e in exps.items()}


def main():
    print(f"Prompt: '{PROMPT}'\n")
    for temperatura in (0.2, 1.0, 2.0):
        # PASO 1: puntajes / temperatura -> softmax -> probabilidades
        probs = softmax(LOGITS, temperatura)
        # PASO 2: mostrar las probabilidades y muestrear 20 veces con ellas
        print(f"--- temperatura {temperatura} ---")
        for token, p in probs.items():
            print(f"  {token:<10} {p:6.1%} {'#' * int(p * 40)}")
        muestras = random.choices(list(probs), weights=list(probs.values()), k=20)
        print(f"  20 respuestas: {dict(Counter(muestras).most_common())}\n")

    print("Temperatura 0 (o casi) = escoger siempre el más probable (greedy).")
    print("lab7 usa temperature=0.2 en src/gemini_client.py: para responder sobre")
    print("documentos queremos precisión, no creatividad.")


if __name__ == "__main__":
    main()
