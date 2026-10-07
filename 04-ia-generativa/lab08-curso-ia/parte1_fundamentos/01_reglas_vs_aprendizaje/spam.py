"""Micro lab 01 — Reglas escritas a mano vs. aprender de ejemplos.

Dos formas de resolver el mismo problema (¿un mensaje es spam?):

  1. Programación clásica: TÚ escribes la regla.
  2. Machine learning: le das EJEMPLOS y el programa saca sus propias reglas.

Correr:  python spam.py
"""
import math
from collections import Counter

# Datos de entrenamiento: mensajes que ya sabemos si son spam o no.
EJEMPLOS = [
    ("gana dinero gratis ahora", "spam"),
    ("oferta exclusiva gana un premio", "spam"),
    ("haz clic para reclamar tu premio gratis", "spam"),
    ("dinero rapido sin esfuerzo oferta", "spam"),
    ("urgente reclama tu dinero hoy", "spam"),
    ("nos vemos mañana en la clase", "normal"),
    ("te mando el reporte del laboratorio", "normal"),
    ("la reunion es a las cinco", "normal"),
    ("gracias por la ayuda con la tarea", "normal"),
    ("mañana revisamos el codigo juntos", "normal"),
]

# Mensajes NUEVOS que ninguno de los dos métodos ha visto.
PRUEBAS = [
    ("reclama tu premio ahora", "spam"),
    ("la clase de mañana es gratis", "normal"),
    ("oferta de dinero rapido", "spam"),
    ("revisamos el reporte en la reunion", "normal"),
]


# ---------------------------------------------------------------------------
# Método 1: regla escrita a mano
# ---------------------------------------------------------------------------
def clasificar_con_regla(texto):
    """Regla inventada por una persona: si aparece "gratis" o "dinero", es spam.

    Funciona solo con lo que a esa persona se le ocurrió. Si el spam usa
    otras palabras ("premio", "oferta"), la regla no lo detecta.
    """
    palabras_sospechosas = ["gratis", "dinero"]
    for palabra in texto.split():
        if palabra in palabras_sospechosas:
            return "spam"
    return "normal"


# ---------------------------------------------------------------------------
# Método 2: aprender de los ejemplos (un "Naive Bayes" simplificado)
# ---------------------------------------------------------------------------
def entrenar(ejemplos):
    """'Entrenar' aquí es solo CONTAR palabras.

    Regresa un diccionario con dos contadores, por ejemplo:
        conteos["spam"]["dinero"]   -> 3  (apareció 3 veces en mensajes spam)
        conteos["normal"]["dinero"] -> 0  (nunca apareció en mensajes normales)

    Counter es un diccionario que empieza en 0 para cualquier palabra,
    así que podemos sumar sin preocuparnos de si la palabra ya existía.
    """
    conteos = {"spam": Counter(), "normal": Counter()}
    for texto, etiqueta in ejemplos:
        for palabra in texto.split():
            conteos[etiqueta][palabra] += 1
    return conteos


def puntaje(texto, conteos, clase):
    """Qué tan 'típico' de una clase ("spam" o "normal") es el mensaje.

    Idea: si las palabras del mensaje aparecían mucho en los ejemplos de
    esa clase, el puntaje sale alto.

    Para cada palabra calculamos:
        probabilidad = (veces que apareció en la clase + 1) / (total de palabras de la clase + tamaño del vocabulario)

      * El "+1" (suavizado de Laplace) evita que una palabra que nunca vimos
        dé probabilidad 0, lo que arruinaría todo el cálculo.
      * Usamos log() y SUMAMOS en lugar de multiplicar probabilidades:
        multiplicar muchos números chicos da algo casi cero que la
        computadora no puede representar bien; sumar logaritmos es
        equivalente y no tiene ese problema.
    El resultado es un número negativo: MÁS CERCA DE 0 = más típico de la clase.
    """
    vocabulario = set(conteos["spam"]) | set(conteos["normal"])   # todas las palabras distintas vistas
    total_palabras_clase = sum(conteos[clase].values())

    resultado = 0
    for palabra in texto.split():
        probabilidad = (conteos[clase][palabra] + 1) / (total_palabras_clase + len(vocabulario))
        resultado += math.log(probabilidad)
    return resultado


def clasificar_aprendido(texto, conteos):
    """Gana la clase cuyo puntaje sea más alto."""
    puntaje_spam = puntaje(texto, conteos, "spam")
    puntaje_normal = puntaje(texto, conteos, "normal")
    if puntaje_spam > puntaje_normal:
        return "spam"
    return "normal"


def main():
    # PASO #1: "entrenar" = contar palabras en los ejemplos etiquetados
    conteos = entrenar(EJEMPLOS)

    # PASO #2: ver qué aprendió (nadie le dijo estas palabras: salieron de los datos)
    print("Lo que el modelo 'aprendió' (palabras más frecuentes por clase):")
    for clase in ["spam", "normal"]:
        mas_comunes = conteos[clase].most_common(6)          # lista de (palabra, veces)
        solo_palabras = [palabra for palabra, veces in mas_comunes]
        print(f"  {clase:>6}: {', '.join(solo_palabras)}")

    # PASO #3: probar AMBOS métodos con mensajes que ninguno vio
    print(f"\n{'Mensaje nuevo':<40} {'Real':>8} {'Regla':>10} {'Aprendido':>10}")
    print("-" * 71)
    aciertos_regla = 0
    aciertos_ml = 0
    for texto, real in PRUEBAS:
        respuesta_regla = clasificar_con_regla(texto)
        respuesta_ml = clasificar_aprendido(texto, conteos)

        if respuesta_regla == real:
            aciertos_regla += 1
            marca_regla = "ok"
        else:
            marca_regla = "X"

        if respuesta_ml == real:
            aciertos_ml += 1
            marca_ml = "ok"
        else:
            marca_ml = "X"

        print(f"{texto:<40} {real:>8} {respuesta_regla:>7} {marca_regla:<2} {respuesta_ml:>7} {marca_ml:<2}")

    print(f"\nAciertos regla:     {aciertos_regla}/{len(PRUEBAS)}")
    print(f"Aciertos aprendido: {aciertos_ml}/{len(PRUEBAS)}")


if __name__ == "__main__":
    main()
