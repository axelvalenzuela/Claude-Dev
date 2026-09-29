"""Micro lab 06 — Embeddings: significado convertido en coordenadas.

Un EMBEDDING es una lista de números (un vector) que representa el
significado de un texto. Cosas parecidas -> vectores que apuntan hacia el
mismo lado. Para medir "qué tan hacia el mismo lado" se usa la SIMILITUD
DE COSENO: 1.0 = idénticos, 0.0 = nada que ver.

Parte A: vectores hechos A MANO, con dimensiones que entendemos.
Parte B: vectores por conteo de palabras, y por qué eso no basta.

Correr:  python embeddings.py
"""
import math
from collections import Counter

# Parte A — cada dimensión significa algo que elegimos nosotros:
#                 [animal, fruta, tamaño, doméstico]
PALABRAS = {
    "perro":   [1.0, 0.0, 0.5, 1.0],
    "gato":    [1.0, 0.0, 0.3, 1.0],
    "leon":    [1.0, 0.0, 0.8, 0.0],
    "raton":   [1.0, 0.0, 0.1, 0.3],
    "manzana": [0.0, 1.0, 0.2, 0.0],
    "sandia":  [0.0, 1.0, 0.7, 0.0],
    "uva":     [0.0, 1.0, 0.1, 0.0],
}


def coseno(a, b):
    punto = sum(x * y for x, y in zip(a, b))
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(y * y for y in b))
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return punto / (norma_a * norma_b)


def parte_a():
    print("PARTE A — vectores a mano  [animal, fruta, tamaño, doméstico]\n")
    for consulta in ("perro", "manzana"):
        print(f"Más parecidos a '{consulta}':")
        ranking = sorted(
            ((coseno(PALABRAS[consulta], v), p) for p, v in PALABRAS.items() if p != consulta),
            reverse=True,
        )
        for sim, palabra in ranking:
            barra = "#" * int(max(sim, 0) * 30)
            print(f"  {palabra:<8} {sim:5.2f} {barra}")
        print()


# Parte B — vector = cuántas veces aparece cada palabra ("bolsa de palabras").
def vector_conteo(frase, vocabulario):
    conteo = Counter(frase.lower().split())
    return [conteo[p] for p in vocabulario]


def parte_b():
    print("PARTE B — vectores por conteo de palabras\n")
    base = "el perro corre en el parque"
    otras = [
        "el perro corre en el jardin",   # casi las mismas palabras
        "un can trota por la plaza",     # MISMO significado, otras palabras
        "el precio del dolar en el banco",  # otro tema, pero comparte "el" y "en"
    ]
    vocabulario = sorted(set(" ".join([base] + otras).split()))
    v_base = vector_conteo(base, vocabulario)
    print(f"Frase base: '{base}'")
    for frase in otras:
        sim = coseno(v_base, vector_conteo(frase, vocabulario))
        print(f"  {sim:4.2f}  '{frase}'")

    print("\nProblema: 'un can trota por la plaza' significa casi lo mismo pero da 0,")
    print("y la frase del dólar sale más parecida solo por compartir 'el' y 'en'.")
    print("Contar palabras no captura SIGNIFICADO.")
    print("\nSolución: un modelo de embeddings (en lab7: text-embedding-005) que")
    print("APRENDIÓ, leyendo muchísimo texto, a poner 'perro' y 'can' cerca.")
    print("Da vectores de ~768 números cuyas dimensiones ya no tienen nombre,")
    print("pero el coseno funciona exactamente igual que aquí.")


if __name__ == "__main__":
    parte_a()   # PASO 1: con dimensiones que entendemos, el coseno encuentra lo parecido
    parte_b()   # PASO 2: contando palabras falla -> por eso existen los modelos de embeddings
