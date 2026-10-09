"""Ejercicio #2 — Listas, diccionarios y ciclos for.

Por qué importa para IA: un texto se vuelve una LISTA de palabras/tokens, y la
respuesta de un modelo llega como DICCIONARIO (JSON) con datos anidados.

  PASO #1: python 01-python-for-ai/02_listas_y_diccionarios/ejercicio.py
  PASO #2: lee demostracion()
  PASO #3: resuelve los retos (busca "TU CÓDIGO AQUÍ")
  PASO #4: vuelve a correr hasta ver todo en [OK]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _verificador import verificar  # noqa: E402


def demostracion():
    # PASO #1 — LISTA: varios valores en orden, entre [ ]
    palabras = "el modelo predice la siguiente palabra".split()   # split() corta por espacios
    print(palabras)
    print("cuántas:", len(palabras), "| primera:", palabras[0], "| última:", palabras[-1])

    # PASO #2 — agregar y recorrer con for (el for repite el bloque por cada elemento)
    palabras.append("otra")
    for palabra in palabras:
        print("  -", palabra.upper())

    # PASO #3 — DICCIONARIO: pares clave -> valor, entre { }. Así se ve una respuesta de un modelo:
    respuesta = {
        "texto": "SAS es una plataforma de analítica",
        "modelo": "gemini-3.1-flash-lite",
        "uso": {"tokens_entrada": 12, "tokens_salida": 30},   # un diccionario DENTRO de otro
    }
    print(respuesta["texto"])
    print("tokens de salida:", respuesta["uso"]["tokens_salida"])

    # PASO #4 — recorrer un diccionario: .items() da (clave, valor)
    for clave, valor in respuesta["uso"].items():
        print(f"  {clave} = {valor}")

    # PASO #5 — .get() lee una clave que quizá no existe, sin tronar
    print("temperatura:", respuesta.get("temperatura", "no viene"))

    # PASO #6 — contar con un diccionario (la base de los micro ejercicios 01 y 07)
    conteo = {}
    for palabra in "a b a c a".split():
        conteo[palabra] = conteo.get(palabra, 0) + 1
    print(conteo)

    # PASO #7 — "list comprehension": crear una lista nueva en una línea
    largas = [p for p in palabras if len(p) > 5]
    print("palabras largas:", largas)


# ============================================================================
# RETOS
# ============================================================================

def contar_palabras(texto):
    """Reto #1: devuelve un diccionario {palabra: veces}. Pasa el texto a minúsculas con .lower().
    Ejemplo: contar_palabras("El gato y el perro") -> {"el": 2, "gato": 1, "y": 1, "perro": 1}"""
    # TU CÓDIGO AQUÍ  (pista: mira el PASO #6)
    return None


def total_tokens(respuesta):
    """Reto #2: suma tokens_entrada + tokens_salida que vienen dentro de respuesta["uso"]."""
    # TU CÓDIGO AQUÍ
    return None


def mas_frecuente(conteo):
    """Reto #3: devuelve la CLAVE con el valor más alto.
    Ejemplo: mas_frecuente({"a": 1, "b": 3, "c": 2}) -> "b"
    Pista: recorre con .items() guardando la mejor hasta el momento
    (o, más corto: max(conteo, key=conteo.get))."""
    # TU CÓDIGO AQUÍ
    return None


RESPUESTA_EJEMPLO = {"texto": "...", "uso": {"tokens_entrada": 120, "tokens_salida": 45}}

RETOS = [
    (1, "contar_palabras", lambda: contar_palabras("El gato y el perro"), {"el": 2, "gato": 1, "y": 1, "perro": 1}),
    (2, "total_tokens lee un diccionario anidado", lambda: total_tokens(RESPUESTA_EJEMPLO), 165),
    (3, "mas_frecuente", lambda: mas_frecuente({"a": 1, "b": 3, "c": 2}), "b"),
]

if __name__ == "__main__":
    demostracion()
    verificar(RETOS)
