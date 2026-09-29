"""Micro lab 02 — Aprender = ajustar números para bajar el error.

Queremos predecir la calificación de un examen a partir de las horas de
estudio. El "modelo" es una recta:

    calificacion = w * horas + b

w y b son los PARÁMETROS. Al inicio valen 0 (el modelo no sabe nada).
Entrenar = repetir muchas veces:
    1. predecir con los w y b actuales
    2. medir el error contra los datos reales
    3. mover w y b un poquito en la dirección que baja el error
       (eso es el "descenso de gradiente")

Un modelo como Gemini o Claude hace exactamente esto, pero con miles de
millones de parámetros en vez de 2.

Correr:  python regresion.py
"""

# (horas de estudio, calificación obtenida)
DATOS = [(1, 32), (2, 38), (3, 52), (4, 58), (5, 71), (6, 78), (7, 88), (8, 99)]

TASA_APRENDIZAJE = 0.01   # qué tan grande es cada pasito de ajuste
EPOCAS = 3000             # cuántas veces recorremos todos los datos


def predecir(horas, w, b):
    return w * horas + b


def error_promedio(w, b):
    """Error cuadrático medio: promedio de (predicción - real)^2."""
    return sum((predecir(x, w, b) - y) ** 2 for x, y in DATOS) / len(DATOS)


def main():
    # PASO 1: empezar sin saber nada (parámetros en cero)
    w, b = 0.0, 0.0
    n = len(DATOS)

    print(f"{'época':>6} {'w':>8} {'b':>8} {'error':>10}")
    # PASO 2: repetir muchas veces: medir error -> calcular gradiente -> ajustar
    for epoca in range(EPOCAS + 1):
        if epoca in (0, 1, 5, 20, 100, 500, 1000, 2000, EPOCAS):
            print(f"{epoca:>6} {w:>8.2f} {b:>8.2f} {error_promedio(w, b):>10.2f}")

        # Gradiente: cuánto cambia el error si muevo w o b un poquito.
        grad_w = sum(2 * (predecir(x, w, b) - y) * x for x, y in DATOS) / n
        grad_b = sum(2 * (predecir(x, w, b) - y) for x, y in DATOS) / n

        # Nos movemos en sentido CONTRARIO al gradiente (cuesta abajo).
        w -= TASA_APRENDIZAJE * grad_w
        b -= TASA_APRENDIZAJE * grad_b

    # PASO 3: usar el modelo entrenado para predecir casos nuevos (esto es "inferencia")
    print(f"\nModelo aprendido: calificacion = {w:.2f} * horas + {b:.2f}")
    for horas in (0, 4.5, 10):
        print(f"  Si estudias {horas:>4} horas -> predice {predecir(horas, w, b):.1f}")
    print("\nOjo con 10 horas: da más de 100. El modelo solo sabe la recta que")
    print("vio en los datos; no 'entiende' que una calificación tiene tope.")


if __name__ == "__main__":
    main()
