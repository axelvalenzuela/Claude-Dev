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
    palabras_sospechosas = {"gratis", "dinero"}
    for palabra in texto.split():
        if palabra in palabras_sospechosas:
            return "spam"
    return "normal"


# ---------------------------------------------------------------------------
# Método 2: aprender de los ejemplos (un "Naive Bayes" simplificado)
# ---------------------------------------------------------------------------
def entrenar(ejemplos):
    """'Entrenar' aquí es solo CONTAR: cuántas veces aparece cada palabra en
    mensajes spam y cuántas en mensajes normales."""
    conteos = {"spam": Counter(), "normal": Counter()}
    for texto, etiqueta in ejemplos:
        conteos[etiqueta].update(texto.split())
    return conteos


def puntaje(texto, conteos, clase):
    """Qué tan 'típico' de esa clase es el mensaje. Cada palabra suma
    log(probabilidad de ver esa palabra en esa clase). El +1 evita que una
    palabra nunca vista dé probabilidad cero."""
    vocabulario = set(conteos["spam"]) | set(conteos["normal"])
    total = sum(conteos[clase].values())
    return sum(
        math.log((conteos[clase][palabra] + 1) / (total + len(vocabulario)))
        for palabra in texto.split()
    )


def clasificar_aprendido(texto, conteos):
    if puntaje(texto, conteos, "spam") > puntaje(texto, conteos, "normal"):
        return "spam"
    return "normal"


def main():
    # PASO 1: "entrenar" = contar palabras en los ejemplos etiquetados
    conteos = entrenar(EJEMPLOS)

    # PASO 2: ver qué aprendió (nadie le dijo estas palabras: salieron de los datos)
    print("Lo que el modelo 'aprendió' (palabras más frecuentes por clase):")
    for clase in ("spam", "normal"):
        top = ", ".join(p for p, _ in conteos[clase].most_common(6))
        print(f"  {clase:>6}: {top}")

    # PASO 3: probar AMBOS métodos con mensajes que ninguno vio
    print("\n{:<40} {:>8} {:>10} {:>10}".format("Mensaje nuevo", "Real", "Regla", "Aprendido"))
    print("-" * 71)
    aciertos_regla = aciertos_ml = 0
    for texto, real in PRUEBAS:
        r = clasificar_con_regla(texto)
        m = clasificar_aprendido(texto, conteos)
        aciertos_regla += r == real
        aciertos_ml += m == real
        marca_r = "ok" if r == real else "X"
        marca_m = "ok" if m == real else "X"
        print(f"{texto:<40} {real:>8} {r:>7} {marca_r:<2} {m:>7} {marca_m:<2}")

    print(f"\nAciertos regla:     {aciertos_regla}/{len(PRUEBAS)}")
    print(f"Aciertos aprendido: {aciertos_ml}/{len(PRUEBAS)}")


if __name__ == "__main__":
    main()
