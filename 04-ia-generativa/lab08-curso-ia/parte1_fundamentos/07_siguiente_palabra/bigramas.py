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
from collections import Counter

random.seed(3)   # misma "suerte" en cada corrida, para que el resultado sea repetible

# Frases de entrenamiento, una por renglón. El "." marca el final de la frase.
CORPUS = """
el gato come pescado .
el gato duerme en la cama .
el perro come carne .
el perro corre en el parque .
la niña come fruta en la cocina .
la niña corre en el parque .
el gato corre en la casa .
""".strip().split("\n")

# Palabra falsa que ponemos al principio de cada frase, para aprender
# también con qué palabras suele EMPEZAR una frase.
INICIO = "<inicio>"


def entrenar(frases):
    """Cuenta qué palabra viene después de cuál.

    Regresa un diccionario de contadores, por ejemplo:
        siguientes["gato"] = Counter({"come": 1, "duerme": 1, "corre": 1})
        siguientes["el"]   = Counter({"gato": 3, "perro": 2, "parque": 2})
    """
    siguientes = {}
    for frase in frases:
        palabras = [INICIO] + frase.split()
        # Recorremos parejas de palabras vecinas: (palabras[0], palabras[1]), (palabras[1], palabras[2]), ...
        for i in range(len(palabras) - 1):
            actual = palabras[i]
            siguiente = palabras[i + 1]
            if actual not in siguientes:
                siguientes[actual] = Counter()
            siguientes[actual][siguiente] += 1
    return siguientes


def probabilidades(siguientes, palabra):
    """Convierte los conteos de una palabra en probabilidades (que suman 1).

    Ejemplo: si después de "gato" vimos come=1, duerme=1, corre=1,
    cada una tiene probabilidad 1/3.
    """
    conteos = siguientes[palabra]
    total = sum(conteos.values())
    resultado = {}
    for posible, veces in conteos.most_common():   # de la más común a la menos
        resultado[posible] = veces / total
    return resultado


def generar(siguientes, max_palabras=12):
    """Inventa una frase palabra por palabra, hasta llegar a "." o a max_palabras."""
    palabra = INICIO
    texto = []
    for _ in range(max_palabras):
        opciones = probabilidades(siguientes, palabra)
        candidatas = list(opciones.keys())
        pesos = list(opciones.values())
        # Escoge al azar, pero respetando las probabilidades (muestreo):
        # una palabra con 60% de probabilidad sale más seguido que una con 10%.
        palabra = random.choices(candidatas, weights=pesos)[0]
        texto.append(palabra)
        if palabra == ".":
            break
    return " ".join(texto)


def main():
    # PASO #1: entrenar = contar qué palabra sigue a cuál
    modelo = entrenar(CORPUS)

    # PASO #2: el "modelo" es una tabla de probabilidades de la siguiente palabra
    for palabra in ["el", "gato", "en"]:
        print(f"Después de '{palabra}' puede venir:")
        for siguiente, p in probabilidades(modelo, palabra).items():
            print(f"  {siguiente:<8} {p:5.0%} {'#' * int(p * 40)}")
        print()

    # PASO #3: generar = escoger la siguiente palabra, agregarla, repetir
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
