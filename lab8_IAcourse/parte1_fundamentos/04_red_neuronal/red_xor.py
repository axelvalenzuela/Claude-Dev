"""Micro lab 04 — Una red neuronal pequeña que SÍ aprende XOR.

Juntamos neuronas en capas:

    entrada (2)  ->  capa oculta (3 neuronas)  ->  salida (1 neurona)

Dos cambios respecto al micro lab 03:
  * En vez de "0 o 1" en seco, cada neurona usa la función SIGMOIDE, que da
    un número suave entre 0 y 1. Así se puede calcular cuánto contribuyó
    cada peso al error.
  * El error de la salida se reparte hacia atrás, capa por capa, para saber
    cómo ajustar CADA peso. A eso se le llama BACKPROPAGATION.

Las redes de los modelos de lenguaje son esto mismo, con muchas más capas y
miles de millones de pesos.

Correr:  python red_xor.py
"""
import math
import random

random.seed(7)   # misma "suerte" en cada corrida, para que el resultado sea repetible

DATOS = [((0, 0), 0), ((0, 1), 1), ((1, 0), 1), ((1, 1), 0)]
OCULTAS = 3
TASA = 0.5
EPOCAS = 10000


def sigmoide(z):
    return 1 / (1 + math.exp(-z))


# Pesos iniciales al azar (si todos empezaran en 0, todas las neuronas
# aprenderían exactamente lo mismo).
w_oculta = [[random.uniform(-1, 1) for _ in range(2)] for _ in range(OCULTAS)]
b_oculta = [random.uniform(-1, 1) for _ in range(OCULTAS)]
w_salida = [random.uniform(-1, 1) for _ in range(OCULTAS)]
b_salida = random.uniform(-1, 1)


def adelante(x):
    """Pasa una entrada por la red y devuelve (activaciones ocultas, salida)."""
    h = [sigmoide(w[0] * x[0] + w[1] * x[1] + b) for w, b in zip(w_oculta, b_oculta)]
    y = sigmoide(sum(wi * hi for wi, hi in zip(w_salida, h)) + b_salida)
    return h, y


def error_total():
    return sum((adelante(x)[1] - esperado) ** 2 for x, esperado in DATOS) / len(DATOS)


def entrenar():
    global b_salida
    for epoca in range(EPOCAS + 1):
        if epoca % 2000 == 0:
            print(f"época {epoca:>5}   error {error_total():.4f}")
        for x, esperado in DATOS:
            h, y = adelante(x)
            # 1) ¿Cuánto se equivocó la salida? (la derivada de la sigmoide es y*(1-y))
            delta_salida = (y - esperado) * y * (1 - y)
            # 2) Repartir esa culpa hacia atrás a cada neurona oculta.
            delta_oculta = [delta_salida * w_salida[j] * h[j] * (1 - h[j]) for j in range(OCULTAS)]
            # 3) Ajustar cada peso un poquito en contra de su culpa.
            for j in range(OCULTAS):
                w_salida[j] -= TASA * delta_salida * h[j]
                w_oculta[j][0] -= TASA * delta_oculta[j] * x[0]
                w_oculta[j][1] -= TASA * delta_oculta[j] * x[1]
                b_oculta[j] -= TASA * delta_oculta[j]
            b_salida -= TASA * delta_salida


def main():
    # PASO 1: con pesos al azar, la red no sabe nada
    print("Antes de entrenar, la red responde al azar:")
    for x, esperado in DATOS:
        print(f"  {x[0]} XOR {x[1]} = {esperado}   red dice {adelante(x)[1]:.3f}")

    # PASO 2: entrenar con backpropagation (ver entrenar(): pasos 1, 2 y 3)
    print("\nEntrenando...")
    entrenar()

    # PASO 3: la misma pregunta, ahora con pesos ajustados
    print("\nDespués de entrenar:")
    for x, esperado in DATOS:
        y = adelante(x)[1]
        print(f"  {x[0]} XOR {x[1]} = {esperado}   red dice {y:.3f}  -> {round(y)}")
    print("\nLa red no da 0 y 1 exactos sino números cercanos: es una PROBABILIDAD.")
    print("Los modelos de lenguaje también responden con probabilidades (micro lab 07).")


if __name__ == "__main__":
    main()
