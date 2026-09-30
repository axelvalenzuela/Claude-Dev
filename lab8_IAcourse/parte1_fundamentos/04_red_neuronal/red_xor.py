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
OCULTAS = 3      # cuántas neuronas tiene la capa oculta
TASA = 0.5       # tamaño de cada paso de ajuste (como TASA_APRENDIZAJE del micro lab 02)
EPOCAS = 10000   # cuántas veces recorremos los 4 ejemplos


def sigmoide(z):
    """Convierte cualquier número en uno entre 0 y 1.

    Números muy negativos -> casi 0; muy positivos -> casi 1; 0 -> 0.5.
    A diferencia del "if suma > 0" del perceptrón, es una curva suave, y eso
    permite saber cuánto cambia la salida si movemos un peso un poquito.
    """
    return 1 / (1 + math.exp(-z))


# ---------------------------------------------------------------------------
# Los pesos de la red (variables globales para que el código sea corto).
# Empiezan al azar: si todos empezaran en 0, todas las neuronas ocultas
# recibirían los mismos ajustes y aprenderían exactamente lo mismo.
# ---------------------------------------------------------------------------
# w_oculta[j] = [peso de x1, peso de x2] de la neurona oculta j
w_oculta = []
for _ in range(OCULTAS):
    w_oculta.append([random.uniform(-1, 1), random.uniform(-1, 1)])

# b_oculta[j] = sesgo de la neurona oculta j
b_oculta = []
for _ in range(OCULTAS):
    b_oculta.append(random.uniform(-1, 1))

# w_salida[j] = cuánto escucha la neurona de salida a la neurona oculta j
w_salida = []
for _ in range(OCULTAS):
    w_salida.append(random.uniform(-1, 1))

# b_salida[0] = sesgo de la neurona de salida.
# Va dentro de una lista para poder modificarla desde entrenar() sin usar "global".
b_salida = [random.uniform(-1, 1)]


def adelante(x):
    """Pasa una entrada por la red ("forward pass").

    Regresa dos cosas:
      h = lista con la salida de cada neurona oculta (la necesitamos para entrenar)
      y = la respuesta final de la red, un número entre 0 y 1
    """
    # Capa oculta: cada neurona hace su suma ponderada de x1 y x2 y le aplica sigmoide.
    h = []
    for j in range(OCULTAS):
        suma = w_oculta[j][0] * x[0] + w_oculta[j][1] * x[1] + b_oculta[j]
        h.append(sigmoide(suma))

    # Capa de salida: una neurona que recibe como entradas las salidas de la capa oculta.
    suma = 0
    for j in range(OCULTAS):
        suma += w_salida[j] * h[j]
    y = sigmoide(suma + b_salida[0])
    return h, y


def error_total():
    """Error cuadrático medio de la red sobre los 4 ejemplos (igual que en el micro lab 02)."""
    suma = 0
    for x, esperado in DATOS:
        h, y = adelante(x)
        suma += (y - esperado) ** 2
    return suma / len(DATOS)


def entrenar():
    """Ajusta todos los pesos con backpropagation.

    Para cada ejemplo:
      1) Calcular cuánto se equivocó la neurona de salida (delta_salida).
      2) Repartir esa "culpa" hacia atrás: cada neurona oculta recibe una parte,
         proporcional a qué tanto la escuchaba la salida (w_salida[j]).
      3) Mover cada peso un poquito en contra de su culpa.

    El factor  y * (1 - y)  que aparece es la derivada de la sigmoide: dice qué
    tan sensible es la neurona a un cambio. Si ya está muy segura (y cerca de 0
    o de 1), ese factor es chico y el peso casi no se mueve.
    """
    for epoca in range(EPOCAS + 1):
        if epoca % 2000 == 0:
            print(f"época {epoca:>5}   error {error_total():.4f}")

        for x, esperado in DATOS:
            h, y = adelante(x)

            # 1) Culpa de la neurona de salida.
            delta_salida = (y - esperado) * y * (1 - y)

            # 2) Culpa de cada neurona oculta.
            delta_oculta = []
            for j in range(OCULTAS):
                delta_oculta.append(delta_salida * w_salida[j] * h[j] * (1 - h[j]))

            # 3) Ajustar los pesos (restamos: vamos cuesta abajo en el error).
            for j in range(OCULTAS):
                w_salida[j] -= TASA * delta_salida * h[j]
                w_oculta[j][0] -= TASA * delta_oculta[j] * x[0]
                w_oculta[j][1] -= TASA * delta_oculta[j] * x[1]
                b_oculta[j] -= TASA * delta_oculta[j]
            b_salida[0] -= TASA * delta_salida


def main():
    # PASO #1: con pesos al azar, la red no sabe nada
    print("Antes de entrenar, la red responde al azar:")
    for x, esperado in DATOS:
        h, y = adelante(x)
        print(f"  {x[0]} XOR {x[1]} = {esperado}   red dice {y:.3f}")

    # PASO #2: entrenar con backpropagation (ver entrenar(): pasos 1, 2 y 3)
    print("\nEntrenando...")
    entrenar()

    # PASO #3: la misma pregunta, ahora con pesos ajustados
    print("\nDespués de entrenar:")
    for x, esperado in DATOS:
        h, y = adelante(x)
        print(f"  {x[0]} XOR {x[1]} = {esperado}   red dice {y:.3f}  -> {round(y)}")
    print("\nLa red no da 0 y 1 exactos sino números cercanos: es una PROBABILIDAD.")
    print("Los modelos de lenguaje también responden con probabilidades (micro lab 07).")


if __name__ == "__main__":
    main()
