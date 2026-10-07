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

Ejemplo de cómo avanza BPE con la palabra "programa":
    inicio:      p r o g r a m a _
    fusión 'r'+'a':  p r o g ra m a _
    fusión 'p'+'r':  pr o g ra m a _
    ...y así hasta tener pedazos como "program" + "a_"

Correr:  python tokens.py
"""
from collections import Counter

# Texto de entrenamiento: una lista de palabras.
CORPUS = """
el programador programa programas y el programa corre
los programadores programan y reprograman los programas
la migracion migra datos y el migrador migra tablas
""".split()

FIN = "_"   # marca de fin de palabra, para distinguir "program" de "programa"
FUSIONES = 12   # cuántas reglas de fusión aprender (más fusiones = pedazos más grandes)

# Cómo representamos las palabras en este archivo:
#   una palabra = una TUPLA de símbolos, por ejemplo ("p", "r", "o", "g", "r", "a", "m", "a", "_")
#   "palabras"  = un Counter {tupla_de_símbolos: cuántas veces aparece en el corpus}
# Usamos tuplas (y no listas) porque las llaves de un diccionario no pueden ser listas.


def contar_pares(palabras):
    """Cuenta cuántas veces aparece cada par de símbolos VECINOS en todo el corpus.

    Ejemplo: ("p","r","o") tiene los pares ("p","r") y ("r","o").
    Si esa palabra aparece 3 veces en el corpus, cada par suma 3.
    """
    pares = Counter()
    for simbolos, frecuencia in palabras.items():
        for i in range(len(simbolos) - 1):
            par = (simbolos[i], simbolos[i + 1])
            pares[par] += frecuencia
    return pares


def fusionar_palabra(simbolos, par):
    """Junta el par en una sola pieza cada vez que aparece dentro de UNA palabra.

    Ejemplo: fusionar_palabra(("p","r","o"), ("p","r"))  ->  ("pr","o")
    """
    resultado = []
    i = 0
    while i < len(simbolos):
        es_el_par = i < len(simbolos) - 1 and simbolos[i] == par[0] and simbolos[i + 1] == par[1]
        if es_el_par:
            resultado.append(simbolos[i] + simbolos[i + 1])   # se juntan en un solo símbolo
            i += 2                                            # saltamos ambos
        else:
            resultado.append(simbolos[i])
            i += 1
    return tuple(resultado)


def fusionar(palabras, par):
    """Aplica fusionar_palabra() a TODAS las palabras del corpus."""
    nuevas = {}
    for simbolos, frecuencia in palabras.items():
        nuevas[fusionar_palabra(simbolos, par)] = frecuencia
    return nuevas


def aprender_bpe(corpus, n_fusiones):
    """Aprende las reglas de fusión: en cada paso junta el par más frecuente.

    Regresa la lista de reglas en el orden en que se aprendieron, por ejemplo
    [("r","a"), ("p","r"), ...]. Ese orden importa: al tokenizar texto nuevo
    se aplican igual, una tras otra.
    """
    # Al inicio cada palabra es una tupla de letras + la marca de fin.
    palabras = Counter()
    for palabra in corpus:
        palabras[tuple(palabra) + (FIN,)] += 1

    reglas = []
    for paso in range(1, n_fusiones + 1):
        pares = contar_pares(palabras)
        if not pares:          # ya todo está fusionado; no queda nada que juntar
            break
        mejor = pares.most_common(1)[0][0]   # most_common(1) = [(par, veces)] -> nos quedamos con el par
        reglas.append(mejor)
        palabras = fusionar(palabras, mejor)
        print(f"  fusión {paso:>2}: '{mejor[0]}' + '{mejor[1]}' -> '{mejor[0] + mejor[1]}'")
    return reglas


def tokenizar(texto, reglas):
    """Corta un texto en tokens usando las reglas aprendidas.

    Cada palabra empieza como letras sueltas y se le aplican las fusiones
    en el mismo orden en que se aprendieron.
    """
    tokens = []
    for palabra in texto.split():
        simbolos = tuple(palabra) + (FIN,)
        for regla in reglas:
            simbolos = fusionar_palabra(simbolos, regla)
        tokens.extend(simbolos)
    return tokens


def main():
    # PASO #1: aprender el vocabulario de subpalabras a partir del corpus
    print("Aprendiendo subpalabras con BPE (se juntan los pares más frecuentes):")
    reglas = aprender_bpe(CORPUS, FUSIONES)

    # PASO #2: cortar una frase con las reglas aprendidas y convertir cada token en un número
    frase = "el programador migra los programas"
    tokens_bpe = tokenizar(frase, reglas)

    # Vocabulario: a cada token distinto le damos un número (su id).
    vocab = {}
    for numero, token in enumerate(sorted(set(tokens_bpe))):
        vocab[token] = numero
    como_numeros = [vocab[token] for token in tokens_bpe]

    print(f"\nFrase: '{frase}'")
    print(f"  por letra:    {len(frase.replace(' ', ''))} tokens")
    print(f"  por palabra:  {len(frase.split())} tokens")
    print(f"  por BPE:      {len(tokens_bpe)} tokens -> {tokens_bpe}")
    print(f"  como números: {como_numeros}")

    # PASO #3: una palabra que nunca vio se arma con pedazos conocidos
    nueva = "reprogramador"
    print(f"\nPalabra que nunca vio: '{nueva}' -> {tokenizar(nueva, reglas)}")
    print("  Aunque no la conoce completa, la arma con pedazos que sí conoce.")

    print("\nPor qué importa: los modelos cobran y tienen límites POR TOKEN, no por")
    print("palabra. En español suele salir ~1.3-2 tokens por palabra.")
    print("En lab7, src/count_tokens.py le pregunta a Gemini cuántos tokens usa.")


if __name__ == "__main__":
    main()
