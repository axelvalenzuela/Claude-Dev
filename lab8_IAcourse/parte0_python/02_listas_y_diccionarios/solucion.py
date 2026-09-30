"""Solución del Ejercicio #2. Intenta resolverlo tú antes de leer esto."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _verificador import verificar  # noqa: E402


def contar_palabras(texto):
    conteo = {}
    for palabra in texto.lower().split():
        conteo[palabra] = conteo.get(palabra, 0) + 1
    return conteo


def total_tokens(respuesta):
    uso = respuesta["uso"]
    return uso["tokens_entrada"] + uso["tokens_salida"]


def mas_frecuente(conteo):
    mejor, mejor_valor = None, float("-inf")
    for clave, valor in conteo.items():
        if valor > mejor_valor:
            mejor, mejor_valor = clave, valor
    return mejor                    # versión corta: max(conteo, key=conteo.get)


RESPUESTA_EJEMPLO = {"texto": "...", "uso": {"tokens_entrada": 120, "tokens_salida": 45}}

RETOS = [
    (1, "contar_palabras", lambda: contar_palabras("El gato y el perro"), {"el": 2, "gato": 1, "y": 1, "perro": 1}),
    (2, "total_tokens lee un diccionario anidado", lambda: total_tokens(RESPUESTA_EJEMPLO), 165),
    (3, "mas_frecuente", lambda: mas_frecuente({"a": 1, "b": 3, "c": 2}), "b"),
]

if __name__ == "__main__":
    verificar(RETOS, estricto=True)
