"""Ejercicio #1 — Tu primer script: variables, tipos, f-strings e if.

Cómo usar este archivo (igual en todos los ejercicios de la parte 0):
  PASO #1: córrelo tal cual (desde lab8_IAcourse/):
           python parte0_python/01_primer_script/ejercicio.py
  PASO #2: lee la función demostracion() y compárala con lo que se imprimió.
  PASO #3: resuelve los RETOS de abajo: busca "TU CÓDIGO AQUÍ", borra `return None`
           y escribe tu respuesta.
  PASO #4: vuelve a correrlo hasta ver todos los retos en [OK].
  Si te atoras más de 10 minutos en un reto: mira solucion.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # para encontrar _verificador.py
from _verificador import verificar  # noqa: E402


def demostracion():
    # PASO #1 — print() muestra algo en la pantalla
    print("Hola, IA")

    # PASO #2 — variables: un nombre que guarda un valor. Cada valor tiene un TIPO.
    modelo = "gemini-3.1-flash-lite"   # str   (texto, entre comillas)
    tokens_entrada = 1200              # int   (número entero)
    precio_por_millon = 0.25           # float (número con decimales)
    usa_rag = True                     # bool  (True o False)

    # PASO #3 — type() te dice el tipo de un valor
    print(type(modelo), type(tokens_entrada), type(precio_por_millon), type(usa_rag))

    # PASO #4 — operaciones: + - * / ; 1_000_000 es lo mismo que 1000000 (el _ solo ayuda a leer)
    costo = tokens_entrada * precio_por_millon / 1_000_000

    # PASO #5 — f-strings: una f antes de las comillas permite meter variables con {}
    #           {costo:.6f} = mostrar con 6 decimales
    print(f"{tokens_entrada} tokens en {modelo} cuestan ${costo:.6f} USD")

    # PASO #6 — if / elif / else: decidir. OJO: lo de adentro va con 4 espacios (sangría).
    if costo > 0.01:
        print("Llamada cara")
    elif costo > 0.0001:
        print("Llamada normal")
    else:
        print("Llamada muy barata")

    # PASO #7 — una FUNCIÓN recibe datos, hace algo y DEVUELVE (return) un resultado
    def doble(numero):
        return numero * 2

    print("doble de 21 =", doble(21))


# ============================================================================
# RETOS — escribe tu código donde dice TU CÓDIGO AQUÍ
# ============================================================================

def costo_usd(tokens, precio_por_millon):
    """Reto #1: devuelve cuánto cuestan `tokens` si el precio es por millón de tokens.
    Ejemplo: costo_usd(2_000_000, 0.25) -> 0.5"""
    # TU CÓDIGO AQUÍ
    return None


def saludo(nombre):
    """Reto #2: devuelve el texto  Hola, <nombre>. Bienvenido al lab 8
    Ejemplo: saludo("Ana") -> "Hola, Ana. Bienvenido al lab 8"   (usa un f-string)"""
    # TU CÓDIGO AQUÍ
    return None


def es_caro(costo, limite):
    """Reto #3: devuelve True si costo es MAYOR que limite, si no False.
    Ejemplo: es_caro(0.5, 0.1) -> True"""
    # TU CÓDIGO AQUÍ
    return None


RETOS = [
    (1, "costo_usd calcula el costo por tokens", lambda: costo_usd(2_000_000, 0.25), 0.5),
    (2, "saludo arma el texto con f-string", lambda: saludo("Ana"), "Hola, Ana. Bienvenido al lab 8"),
    (3, "es_caro compara contra el límite", lambda: (es_caro(0.5, 0.1), es_caro(0.01, 0.1)), (True, False)),
]

if __name__ == "__main__":
    demostracion()
    verificar(RETOS)
