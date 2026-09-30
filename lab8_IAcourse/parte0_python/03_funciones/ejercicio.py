"""Ejercicio #3 — Funciones: el bloque con el que se arma todo.

Por qué importa para IA: cada paso de un sistema de IA (partir texto, comparar
vectores, llamar al modelo) es una función. Aquí escribes las funciones de
matemáticas que usan los embeddings (micro lab 06 y lab 13).

  PASO #1: python parte0_python/03_funciones/ejercicio.py
  PASO #2: lee demostracion()
  PASO #3: resuelve los retos EN ORDEN (el #3 usa el #2)
  PASO #4: vuelve a correr hasta ver todo en [OK]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _verificador import verificar  # noqa: E402


# PASO #1 — anatomía de una función
def costo_llamada(tokens_entrada, tokens_salida, precio_entrada=0.25, precio_salida=1.50):
    """El texto entre triples comillas es el DOCSTRING: explica qué hace la función.
    precio_entrada=0.25 es un valor POR DEFECTO: si no lo pasas, usa 0.25."""
    entrada = tokens_entrada * precio_entrada / 1_000_000
    salida = tokens_salida * precio_salida / 1_000_000
    return entrada + salida           # return = el resultado que "sale" de la función


# PASO #2 — una función puede devolver varios valores (en realidad, una tupla)
def minimo_y_maximo(numeros):
    return min(numeros), max(numeros)


def demostracion():
    # PASO #3 — llamar funciones: con argumentos en orden o por nombre
    print(costo_llamada(1000, 500))
    print(costo_llamada(1000, 500, precio_salida=3.0))

    # PASO #4 — recibir varios valores
    menor, mayor = minimo_y_maximo([0.2, 0.9, 0.5])
    print("menor:", menor, "mayor:", mayor)

    # PASO #5 — el módulo math trae funciones listas: raíz cuadrada, exponencial, etc.
    print("raíz de 16:", math.sqrt(16), "| e^1:", round(math.exp(1), 4))

    # PASO #6 — zip() recorre dos listas al mismo tiempo, en pareja
    for x, y in zip([1, 2, 3], [10, 20, 30]):
        print(f"  {x} x {y} = {x * y}")


# ============================================================================
# RETOS
# ============================================================================

def promedio(numeros):
    """Reto #1: promedio de una lista. Si la lista está vacía devuelve 0.0.
    Ejemplo: promedio([2, 4, 6]) -> 4.0      (pista: sum() y len())"""
    # TU CÓDIGO AQUÍ
    return None


def producto_punto(a, b):
    """Reto #2: suma de multiplicar elemento por elemento.
    Ejemplo: producto_punto([1, 2, 3], [4, 5, 6]) -> 1*4 + 2*5 + 3*6 = 32   (pista: PASO #6)"""
    # TU CÓDIGO AQUÍ
    return None


def coseno(a, b):
    """Reto #3: similitud de coseno = producto_punto(a, b) / (largo(a) * largo(b)),
    donde largo(v) = math.sqrt(producto_punto(v, v)). Usa tu función del reto #2.
    Ejemplo: coseno([1, 0], [0.9, 0.1]) -> 0.9939"""
    # TU CÓDIGO AQUÍ
    return None


RETOS = [
    (1, "promedio (y lista vacía)", lambda: (promedio([2, 4, 6]), promedio([])), (4.0, 0.0)),
    (2, "producto_punto", lambda: producto_punto([1, 2, 3], [4, 5, 6]), 32),
    (3, "coseno (la base de los embeddings)", lambda: coseno([1, 0], [0.9, 0.1]), 0.99388),
]

if __name__ == "__main__":
    demostracion()
    verificar(RETOS)
