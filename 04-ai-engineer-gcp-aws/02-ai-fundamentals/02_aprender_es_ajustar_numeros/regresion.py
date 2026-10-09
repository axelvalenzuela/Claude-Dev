"""Ejercicio 02 — Aprender = ajustar números para bajar el error.

Queremos predecir la calificación de un examen a partir de las horas de
estudio. El "modelo" es una recta:

    calificacion = w * horas + b

    w (peso)  = cuántos puntos sube la calificación por cada hora extra
    b (sesgo) = la calificación que sacarías con 0 horas

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

# Cada pareja es (horas de estudio, calificación obtenida).
# Son los "ejemplos con respuesta" de los que el modelo va a aprender.
DATOS = [(1, 32), (2, 38), (3, 52), (4, 58), (5, 71), (6, 78), (7, 88), (8, 99)]

TASA_APRENDIZAJE = 0.01   # qué tan grande es cada pasito de ajuste
EPOCAS = 3000             # cuántas veces recorremos todos los datos

# Épocas en las que imprimimos cómo va el entrenamiento (para no imprimir 3000 líneas).
EPOCAS_A_MOSTRAR = [0, 1, 5, 20, 100, 500, 1000, 2000, EPOCAS]


def predecir(horas, w, b):
    """El modelo en sí: la fórmula de la recta.

    Recibe las horas y regresa la calificación que el modelo "cree" que vas a sacar.
    """
    return w * horas + b


def error_promedio(w, b):
    """Qué tan mal le va al modelo con estos w y b (número más chico = mejor).

    Para cada ejemplo calculamos (predicción - real) y lo elevamos al cuadrado:
      * al cuadrado para que los errores negativos no cancelen a los positivos
      * y para que un error grande "pese" más que uno chico
    Luego sacamos el promedio. A esto se le llama ERROR CUADRÁTICO MEDIO (MSE).
    """
    suma = 0
    for horas, real in DATOS:
        diferencia = predecir(horas, w, b) - real
        suma += diferencia ** 2
    return suma / len(DATOS)


def calcular_gradiente(w, b):
    """Dice hacia DÓNDE mover w y b para que el error baje.

    Regresa dos números (grad_w, grad_b):
      * si grad_w es positivo, subir w haría el error MÁS grande -> hay que bajarlo
      * si grad_w es negativo, subir w haría el error más chico  -> hay que subirlo
    Lo mismo para b.

    De dónde salen las fórmulas (derivada del error cuadrático):
      error de un ejemplo    = (w*x + b - y)^2
      derivada respecto a w  = 2 * (w*x + b - y) * x
      derivada respecto a b  = 2 * (w*x + b - y)
    y luego sacamos el promedio sobre todos los ejemplos.
    No necesitas saber derivar: basta con entender que el gradiente es la
    "pendiente" del error, y que caminamos cuesta abajo.
    """
    suma_w = 0
    suma_b = 0
    for horas, real in DATOS:
        diferencia = predecir(horas, w, b) - real
        suma_w += 2 * diferencia * horas
        suma_b += 2 * diferencia
    grad_w = suma_w / len(DATOS)
    grad_b = suma_b / len(DATOS)
    return grad_w, grad_b


def main():
    # PASO #1: empezar sin saber nada (parámetros en cero)
    w = 0.0
    b = 0.0

    # PASO #2: repetir muchas veces: medir error -> calcular gradiente -> ajustar
    print(f"{'época':>6} {'w':>8} {'b':>8} {'error':>10}")
    for epoca in range(EPOCAS + 1):
        if epoca in EPOCAS_A_MOSTRAR:
            print(f"{epoca:>6} {w:>8.2f} {b:>8.2f} {error_promedio(w, b):>10.2f}")

        grad_w, grad_b = calcular_gradiente(w, b)

        # Nos movemos en sentido CONTRARIO al gradiente (cuesta abajo).
        # TASA_APRENDIZAJE hace el paso pequeño para no "pasarnos" del mínimo.
        w = w - TASA_APRENDIZAJE * grad_w
        b = b - TASA_APRENDIZAJE * grad_b

    # PASO #3: usar el modelo entrenado para predecir casos nuevos (esto es "inferencia")
    print(f"\nModelo aprendido: calificacion = {w:.2f} * horas + {b:.2f}")
    for horas in [0, 4.5, 10]:
        prediccion = predecir(horas, w, b)
        print(f"  Si estudias {horas:>4} horas -> predice {prediccion:.1f}")
    print("\nOjo con 10 horas: da más de 100. El modelo solo sabe la recta que")
    print("vio en los datos; no 'entiende' que una calificación tiene tope.")


if __name__ == "__main__":
    main()
