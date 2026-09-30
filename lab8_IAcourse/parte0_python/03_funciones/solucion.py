"""Solución del Ejercicio #3. Intenta resolverlo tú antes de leer esto."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _verificador import verificar  # noqa: E402


def promedio(numeros):
    if not numeros:                 # una lista vacía cuenta como "falso"
        return 0.0
    return sum(numeros) / len(numeros)


def producto_punto(a, b):
    total = 0
    for x, y in zip(a, b):
        total += x * y
    return total                    # versión corta: sum(x * y for x, y in zip(a, b))


def coseno(a, b):
    largo_a = math.sqrt(producto_punto(a, a))
    largo_b = math.sqrt(producto_punto(b, b))
    return producto_punto(a, b) / (largo_a * largo_b)


RETOS = [
    (1, "promedio (y lista vacía)", lambda: (promedio([2, 4, 6]), promedio([])), (4.0, 0.0)),
    (2, "producto_punto", lambda: producto_punto([1, 2, 3], [4, 5, 6]), 32),
    (3, "coseno (la base de los embeddings)", lambda: coseno([1, 0], [0.9, 0.1]), 0.99388),
]

if __name__ == "__main__":
    verificar(RETOS, estricto=True)
