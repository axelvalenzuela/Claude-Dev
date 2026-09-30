"""Solución del Ejercicio #1. Intenta resolverlo tú antes de leer esto."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _verificador import verificar  # noqa: E402


def costo_usd(tokens, precio_por_millon):
    return tokens * precio_por_millon / 1_000_000


def saludo(nombre):
    return f"Hola, {nombre}. Bienvenido al lab 8"


def es_caro(costo, limite):
    return costo > limite          # una comparación ya ES un True o False


RETOS = [
    (1, "costo_usd calcula el costo por tokens", lambda: costo_usd(2_000_000, 0.25), 0.5),
    (2, "saludo arma el texto con f-string", lambda: saludo("Ana"), "Hola, Ana. Bienvenido al lab 8"),
    (3, "es_caro compara contra el límite", lambda: (es_caro(0.5, 0.1), es_caro(0.01, 0.1)), (True, False)),
]

if __name__ == "__main__":
    verificar(RETOS, estricto=True)
