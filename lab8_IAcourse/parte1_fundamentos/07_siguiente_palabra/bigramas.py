"""Micro lab 07 — Un modelo de lenguaje = predecir la siguiente palabra.

Un LLM (Gemini, Claude, GPT) hace, en el fondo, UNA sola cosa:
dado el texto hasta ahora, calcular la probabilidad de cada posible
siguiente token, escoger uno, agregarlo, y repetir.

Aquí construimos el modelo de lenguaje más simple posible: un modelo de
BIGRAMAS, que solo mira la última palabra y cuenta qué palabra suele venir
después en los textos de entrenamiento.

Correr:  python bigramas.py
"""
import random
from collections import Counter, defaultdict

random.seed(3)

CORPUS = """
el gato come pescado .
el gato duerme en la cama .
el perro come carne .
el perro corre en el parque .
la niña come fruta en la cocina .
la niña corre en el parque .
el gato corre en la casa .
""".strip().split("\n")

INICIO = "<inicio>"


def entrenar(frases):
    """siguientes['gato'] = Counter({'come': 1, 'duerme': 1, 'corre': 1})"""
    siguientes = defaultdict(Counter)
    for frase in frases:
        palabras = [INICIO] + frase.split()
        for actual, siguiente in zip(palabras, palabras[1:]):
            siguientes[actual][siguiente] += 1
    return siguientes


def probabilidades(siguientes, palabra):
    total = sum(siguientes[palabra].values())
    return {p: c / total for p, c in siguientes[palabra].most_common()}


def generar(siguientes, max_palabras=12):
    palabra, texto = INICIO, []
    for _ in range(max_palabras):
        opciones = probabilidades(siguientes, palabra)
        # Escoge al azar, pero respetando las probabilidades (muestreo).
        palabra = random.choices(list(opciones), weights=list(opciones.values()))[0]
        texto.append(palabra)
        if palabra == ".":
            break
    return " ".join(texto)


def main():
    # PASO 1: entrenar = contar qué palabra sigue a cuál
    modelo = entrenar(CORPUS)

    # PASO 2: el "modelo" es una tabla de probabilidades de la siguiente palabra
    for palabra in ("el", "gato", "en"):
        print(f"Después de '{palabra}' puede venir:")
        for siguiente, p in probabilidades(modelo, palabra).items():
            print(f"  {siguiente:<8} {p:5.0%} {'#' * int(p * 40)}")
        print()

    # PASO 3: generar = escoger la siguiente palabra, agregarla, repetir
    print("Frases generadas (palabra por palabra, muestreando):")
    for _ in range(6):
        print("  ", generar(modelo))

    print("\nAlgunas frases son NUEVAS (no estaban en el corpus) y otras no tienen")
    print("sentido: el modelo solo mira UNA palabra hacia atrás.")
    print("Un LLM real hace lo mismo pero mira miles de tokens hacia atrás y usa")
    print("una red neuronal gigante (Transformer) en vez de una tabla de conteos.")
    print("Por eso puede 'alucinar': produce lo que SUENA probable, no lo que es verdad.")


if __name__ == "__main__":
    main()
