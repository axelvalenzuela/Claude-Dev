"""Micro lab 03 — Una neurona artificial (perceptrón).

Una neurona recibe entradas, multiplica cada una por un PESO, suma todo
más un SESGO (bias) y decide:

    si  w1*x1 + w2*x2 + b > 0   ->  responde 1
    si no                       ->  responde 0

Es el mismo "ajustar números" del micro lab 02, pero la salida es una
decisión sí/no. Aquí la entrenamos para aprender las compuertas lógicas
AND, OR y XOR. Spoiler: con XOR no va a poder.

Correr:  python perceptron.py
"""

# Tablas de verdad. Cada renglón es ((entrada1, entrada2), salida_correcta).
TABLAS = {
    "AND": [((0, 0), 0), ((0, 1), 0), ((1, 0), 0), ((1, 1), 1)],   # 1 solo si ambas son 1
    "OR":  [((0, 0), 0), ((0, 1), 1), ((1, 0), 1), ((1, 1), 1)],   # 1 si alguna es 1
    "XOR": [((0, 0), 0), ((0, 1), 1), ((1, 0), 1), ((1, 1), 0)],   # 1 si son DIFERENTES
}


def neurona(x1, x2, w1, w2, b):
    """La neurona: suma ponderada de las entradas y decide 1 o 0.

    w1 y w2 dicen cuánto "importa" cada entrada; b mueve el umbral de decisión.
    """
    suma = w1 * x1 + w2 * x2 + b
    if suma > 0:
        return 1
    return 0


def entrenar(tabla, epocas=25, tasa=0.1):
    """Ajusta w1, w2 y b hasta que la neurona conteste bien toda la tabla.

    Regresa (w1, w2, b, epoca):
      * epoca = número de época en que ya no hubo errores
      * epoca = None si se acabaron las épocas y seguía equivocándose

    Regla del perceptrón, para cada ejemplo:
        error = esperado - respuesta     (vale -1, 0 o +1)
      * error = 0  -> contestó bien, no se toca nada
      * error = +1 -> dijo 0 y era 1: sube los pesos de las entradas activas
      * error = -1 -> dijo 1 y era 0: baja los pesos de las entradas activas
    Se multiplica por x1/x2 para que solo cambien los pesos de las entradas
    que valían 1 (las que realmente "participaron" en la decisión).
    """
    w1 = 0.0
    w2 = 0.0
    b = 0.0
    for epoca in range(1, epocas + 1):
        errores = 0
        for (x1, x2), esperado in tabla:
            respuesta = neurona(x1, x2, w1, w2, b)
            error = esperado - respuesta
            if error != 0:
                errores += 1
                w1 = w1 + tasa * error * x1
                w2 = w2 + tasa * error * x2
                b = b + tasa * error
        # Si en toda una vuelta no se equivocó ni una vez, ya aprendió.
        if errores == 0:
            return w1, w2, b, epoca
    return w1, w2, b, None


def main():
    for nombre, tabla in TABLAS.items():
        # PASO #1: entrenar la neurona con la tabla de verdad de esta compuerta
        w1, w2, b, epoca = entrenar(tabla)

        # PASO #2: revisar si ahora responde bien los 4 casos
        if epoca is not None:
            estado = f"aprendió en la época {epoca}"
        else:
            estado = "NO logró aprender"
        print(f"\n=== {nombre}: {estado} ===")
        print(f"pesos: w1={w1:.1f}  w2={w2:.1f}  b={b:.1f}")

        aciertos = 0
        for (x1, x2), esperado in tabla:
            salida = neurona(x1, x2, w1, w2, b)
            if salida == esperado:
                aciertos += 1
                marca = "ok"
            else:
                marca = "X"
            print(f"  {x1} {nombre} {x2} = {esperado}   neurona dice {salida}  {marca}")
        print(f"  aciertos: {aciertos}/4")

    print("\nPor qué falla XOR: una sola neurona solo puede separar los casos con")
    print("UNA línea recta. En XOR los 1 están en esquinas opuestas; ninguna recta")
    print("los separa. Solución: juntar varias neuronas en capas -> micro lab 04.")


if __name__ == "__main__":
    main()
