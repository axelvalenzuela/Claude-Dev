"""Micro lab 05 — Tokens: cómo un modelo "lee" texto.

Una red neuronal solo sabe trabajar con números, así que el texto primero
se corta en pedazos (TOKENS) y a cada pedazo se le asigna un número (id).

Opciones para cortar:
  * por letra:   pocos tokens distintos, pero textos MUY largos
  * por palabra: textos cortos, pero un vocabulario enorme y palabras
                 nuevas que no conoce ("desmigrabilizar")
  * por SUBPALABRAS (lo que usan Gemini, Claude, GPT): un punto medio.
    Se aprende juntando los pares de letras más frecuentes. Este algoritmo
    se llama BPE (Byte Pair Encoding) y aquí hay una versión mini.

Correr:  python tokens.py
"""
from collections import Counter

CORPUS = """
el programador programa programas y el programa corre
los programadores programan y reprograman los programas
la migracion migra datos y el migrador migra tablas
""".split()

FIN = "_"   # marca de fin de palabra, para distinguir "program" de "programa"
FUSIONES = 12


def contar_pares(palabras):
    pares = Counter()
    for simbolos, frecuencia in palabras.items():
        for a, b in zip(simbolos, simbolos[1:]):
            pares[(a, b)] += frecuencia
    return pares


def fusionar(palabras, par):
    nuevas = {}
    for simbolos, frecuencia in palabras.items():
        resultado, i = [], 0
        while i < len(simbolos):
            if i < len(simbolos) - 1 and (simbolos[i], simbolos[i + 1]) == par:
                resultado.append(simbolos[i] + simbolos[i + 1])
                i += 2
            else:
                resultado.append(simbolos[i])
                i += 1
        nuevas[tuple(resultado)] = frecuencia
    return nuevas


def aprender_bpe(corpus, n_fusiones):
    # Al inicio cada palabra es una lista de letras.
    palabras = Counter(tuple(p) + (FIN,) for p in corpus)
    reglas = []
    for paso in range(1, n_fusiones + 1):
        pares = contar_pares(palabras)
        if not pares:
            break
        mejor = pares.most_common(1)[0][0]
        reglas.append(mejor)
        palabras = fusionar(palabras, mejor)
        print(f"  fusión {paso:>2}: '{mejor[0]}' + '{mejor[1]}' -> '{mejor[0] + mejor[1]}'")
    return reglas


def tokenizar(texto, reglas):
    tokens = []
    for palabra in texto.split():
        simbolos = {tuple(palabra) + (FIN,): 1}
        for regla in reglas:          # aplica las fusiones en el orden aprendido
            simbolos = fusionar(simbolos, regla)
        tokens.extend(next(iter(simbolos)))
    return tokens


def main():
    # PASO 1: aprender el vocabulario de subpalabras a partir del corpus
    print("Aprendiendo subpalabras con BPE (se juntan los pares más frecuentes):")
    reglas = aprender_bpe(CORPUS, FUSIONES)

    # PASO 2: cortar una frase con las reglas aprendidas y convertir cada token en un número
    frase = "el programador migra los programas"
    tokens_bpe = tokenizar(frase, reglas)
    vocab = {t: i for i, t in enumerate(sorted(set(tokens_bpe)))}

    print(f"\nFrase: '{frase}'")
    print(f"  por letra:    {len(frase.replace(' ', ''))} tokens")
    print(f"  por palabra:  {len(frase.split())} tokens")
    print(f"  por BPE:      {len(tokens_bpe)} tokens -> {tokens_bpe}")
    print(f"  como números: {[vocab[t] for t in tokens_bpe]}")

    # PASO 3: una palabra que nunca vio se arma con pedazos conocidos
    nueva = "reprogramador"
    print(f"\nPalabra que nunca vio: '{nueva}' -> {tokenizar(nueva, reglas)}")
    print("  Aunque no la conoce completa, la arma con pedazos que sí conoce.")

    print("\nPor qué importa: los modelos cobran y tienen límites POR TOKEN, no por")
    print("palabra. En español suele salir ~1.3-2 tokens por palabra.")
    print("En lab7, src/count_tokens.py le pregunta a Gemini cuántos tokens usa.")


if __name__ == "__main__":
    main()
