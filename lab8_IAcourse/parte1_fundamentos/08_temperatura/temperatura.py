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

random.seed(1)   # misma "suerte" en cada corrida, para que el resultado sea repetible

PROMPT = "El cielo hoy está..."
# Puntajes inventados que un modelo podría dar a cada siguiente palabra.
# Más alto = el modelo la considera más probable. Pueden ser negativos.
LOGITS = {"azul": 4.0, "nublado": 3.2, "despejado": 3.0, "gris": 2.5, "morado": 0.5, "delicioso": -1.0}


def softmax(logits, temperatura):
    """Convierte puntajes en probabilidades que suman 1.

    Pasos:
      1. Dividir cada puntaje entre la temperatura.
         - Temperatura chica -> las diferencias entre puntajes se AGRANDAN.
         - Temperatura grande -> las diferencias se ACHICAN.
      2. Aplicar exp() a cada uno: vuelve todo positivo y exagera las diferencias.
      3. Dividir cada resultado entre la suma total para que sumen 1 (100%).

    Truco técnico: antes de exp() restamos el puntaje máximo. No cambia el
    resultado final, pero evita que exp() de un número enorme y la
    computadora marque error (overflow).
    """
    # 1. Escalar por temperatura
    escalados = {}
    for token, puntaje in logits.items():
        escalados[token] = puntaje / temperatura

    # 2. exp() (restando el máximo por seguridad)
    maximo = max(escalados.values())
    exponenciales = {}
    for token, valor in escalados.items():
        exponenciales[token] = math.exp(valor - maximo)

    # 3. Normalizar para que sumen 1
    total = sum(exponenciales.values())
    probabilidades = {}
    for token, valor in exponenciales.items():
        probabilidades[token] = valor / total
    return probabilidades


def main():
    print(f"Prompt: '{PROMPT}'\n")
    for temperatura in [0.2, 1.0, 2.0]:
        # PASO #1: puntajes / temperatura -> softmax -> probabilidades
        probs = softmax(LOGITS, temperatura)

        # PASO #2: mostrar las probabilidades y muestrear 20 veces con ellas
        print(f"--- temperatura {temperatura} ---")
        for token, p in probs.items():
            print(f"  {token:<10} {p:6.1%} {'#' * int(p * 40)}")

        # random.choices escoge 20 tokens al azar, respetando las probabilidades.
        muestras = random.choices(list(probs.keys()), weights=list(probs.values()), k=20)
        conteo = dict(Counter(muestras).most_common())   # {token: veces que salió}
        print(f"  20 respuestas: {conteo}\n")

    print("Temperatura 0 (o casi) = escoger siempre el más probable (greedy).")
    print("lab7 usa temperature=0.2 en src/gemini_client.py: para responder sobre")
    print("documentos queremos precisión, no creatividad.")


if __name__ == "__main__":
    main()
