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

TABLAS = {
    "AND": [((0, 0), 0), ((0, 1), 0), ((1, 0), 0), ((1, 1), 1)],
    "OR":  [((0, 0), 0), ((0, 1), 1), ((1, 0), 1), ((1, 1), 1)],
    "XOR": [((0, 0), 0), ((0, 1), 1), ((1, 0), 1), ((1, 1), 0)],
}


def neurona(x1, x2, w1, w2, b):
    return 1 if w1 * x1 + w2 * x2 + b > 0 else 0


def entrenar(tabla, epocas=25, tasa=0.1):
    w1 = w2 = b = 0.0
    for epoca in range(1, epocas + 1):
        errores = 0
        for (x1, x2), esperado in tabla:
            error = esperado - neurona(x1, x2, w1, w2, b)   # -1, 0 o +1
            if error != 0:
                errores += 1
                # Regla del perceptrón: empuja los pesos hacia la respuesta correcta.
                w1 += tasa * error * x1
                w2 += tasa * error * x2
                b += tasa * error
        if errores == 0:
            return w1, w2, b, epoca
    return w1, w2, b, None


def main():
    for nombre, tabla in TABLAS.items():
        # PASO 1: entrenar la neurona con la tabla de verdad de esta compuerta
        w1, w2, b, epoca = entrenar(tabla)
        # PASO 2: revisar si ahora responde bien los 4 casos
        estado = f"aprendió en la época {epoca}" if epoca else "NO logró aprender"
        print(f"\n=== {nombre}: {estado} ===")
        print(f"pesos: w1={w1:.1f}  w2={w2:.1f}  b={b:.1f}")
        aciertos = 0
        for (x1, x2), esperado in tabla:
            salida = neurona(x1, x2, w1, w2, b)
            aciertos += salida == esperado
            print(f"  {x1} {nombre} {x2} = {esperado}   neurona dice {salida}"
                  f"  {'ok' if salida == esperado else 'X'}")
        print(f"  aciertos: {aciertos}/4")

    print("\nPor qué falla XOR: una sola neurona solo puede separar los casos con")
    print("UNA línea recta. En XOR los 1 están en esquinas opuestas; ninguna recta")
    print("los separa. Solución: juntar varias neuronas en capas -> micro lab 04.")


if __name__ == "__main__":
    main()
