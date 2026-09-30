"""Micro lab 09 — Mini RAG local: el esqueleto de lab7 sin nube.

RAG = Retrieval-Augmented Generation = "buscar y luego generar".
Un LLM no conoce TUS documentos, así que antes de preguntarle:

    1. CHUNKING   partir los documentos en fragmentos         (micro lab 05)
    2. VECTORES   convertir cada fragmento en un vector       (micro lab 06)
    3. RETRIEVAL  buscar los fragmentos más parecidos a la
                  pregunta con similitud de coseno            (micro lab 06)
    4. PROMPT     pegar esos fragmentos como CONTEXTO + la pregunta
    5. GENERAR    mandar el prompt al LLM                     (micro labs 07-08)

Aquí hacemos 1-4 con Python puro. En el paso 5 solo IMPRIMIMOS el prompt
que se le mandaría al modelo, porque no usamos ninguna API.

Correr:  python mini_rag.py
         python mini_rag.py "¿a qué hora abren?"
"""
import math
import re
import sys
import unicodedata
from collections import Counter

# Base de conocimiento ficticia (la cafetería Kōhi de lab4).
# Llave = nombre del "archivo", valor = su texto.
DOCUMENTOS = {
    "horarios.md": (
        "Kohi abre de lunes a viernes de 7 de la mañana a 8 de la noche. "
        "Los sábados abre de 9 a 14 horas. Los domingos está cerrado."
    ),
    "menu.md": (
        "El café de especialidad cuesta 55 pesos. El latte cuesta 65 pesos. "
        "Tenemos leche de avena y de almendra sin costo extra. "
        "El pan de la casa es de masa madre y se hornea cada mañana."
    ),
    "inauguracion.md": (
        "La inauguración será el 15 de noviembre. Las primeras 50 personas en la "
        "lista de espera reciben un café gratis. Para registrarte deja tu correo en la web."
    ),
    "politicas.md": (
        "Se aceptan mascotas en la terraza. El wifi es gratuito y la contraseña "
        "se pide en caja. No se aceptan pagos con cheque."
    ),
}

# Palabras tan comunes que no ayudan a encontrar nada ("el", "de", "que"...).
# Las quitamos para que dos textos no parezcan parecidos solo por compartirlas.
PALABRAS_VACIAS = set(
    "el la los las de del en y a un una es se con por para que al lo su tu "
    "mi sin cada son esta esta hay como cual cuanto cuanta cuando donde "
    "puedo puede tienen tiene hoy".split()
)
TOP_K = 2       # cuántos fragmentos le pasamos al LLM como contexto
UMBRAL = 0.15   # si el mejor fragmento se parece menos que esto, mejor decir "no sé"


def quitar_acentos(texto):
    """'mañana' -> 'manana', 'sábado' -> 'sabado'.

    NFD separa cada letra acentuada en (letra + acento); luego tiramos los
    acentos, que Unicode clasifica como categoría "Mn".
    """
    separado = unicodedata.normalize("NFD", texto)
    sin_acentos = ""
    for caracter in separado:
        if unicodedata.category(caracter) != "Mn":
            sin_acentos += caracter
    return sin_acentos


def normalizar(texto):
    """Deja solo las palabras "importantes" de un texto, en forma estándar.

    Ejemplo: "¿A qué horas abren los Sábados?"  ->  ["horas", "abren", "sabados"]

    Así "Sábados" y "sabados" cuentan como la misma palabra.
    """
    texto = quitar_acentos(texto.lower())
    palabras = re.findall(r"[a-z0-9]+", texto)   # corta en palabras e ignora signos (¿ ? . ,)
    importantes = []
    for palabra in palabras:
        if palabra not in PALABRAS_VACIAS:
            importantes.append(palabra)
    return importantes


def partir(texto, tamano=14, traslape=4):
    """1. CHUNKING: corta un texto en fragmentos de `tamano` palabras.

    Los fragmentos se enciman `traslape` palabras, para no partir una idea
    justo a la mitad. Con tamano=14 y traslape=4:
        fragmento 1 = palabras  0 a 13
        fragmento 2 = palabras 10 a 23
        fragmento 3 = palabras 20 a 33 ...
    (Igual que lab7/src/chunking.py, pero con fragmentos mucho más chicos.)
    """
    palabras = texto.split()
    paso = tamano - traslape
    fragmentos = []
    inicio = 0
    while True:
        fragmentos.append(" ".join(palabras[inicio:inicio + tamano]))
        inicio += paso
        # Si lo que queda ya venía completo en el fragmento anterior, terminamos.
        if inicio >= len(palabras) - traslape:
            break
    return fragmentos


def vectorizar(texto):
    """2. VECTORES: aquí un simple conteo de palabras.

    Regresa un Counter, por ejemplo {"latte": 1, "cuesta": 1, "65": 1, "pesos": 1}.
    Funciona como el vector de conteo del micro lab 06, pero guardando solo
    las palabras que sí aparecen. En lab7 esto lo hace el modelo
    text-embedding-005 de Vertex AI.
    """
    return Counter(normalizar(texto))


def coseno(a, b):
    """Similitud de coseno entre dos Counter (misma idea que en el micro lab 06).

    Una palabra que falta en un Counter vale 0, así que en el producto punto
    solo cuentan las palabras que están en AMBOS textos.
    """
    producto_punto = 0
    for palabra in a:
        producto_punto += a[palabra] * b[palabra]

    largo_a = math.sqrt(sum(v * v for v in a.values()))
    largo_b = math.sqrt(sum(v * v for v in b.values()))
    if largo_a == 0 or largo_b == 0:
        return 0.0
    return producto_punto / (largo_a * largo_b)


def construir_indice():
    """Parte todos los documentos y guarda cada fragmento con su vector.

    El índice es una lista de diccionarios:
        {"fuente": "menu.md", "texto": "El café de ...", "vector": Counter(...)}
    Se construye UNA vez; después cada pregunta solo se compara contra él.
    """
    indice = []
    for fuente, texto in DOCUMENTOS.items():
        for fragmento in partir(texto):
            indice.append({"fuente": fuente, "texto": fragmento, "vector": vectorizar(fragmento)})
    return indice


def buscar(pregunta, indice, k=TOP_K):
    """3. RETRIEVAL: compara la pregunta contra TODOS los fragmentos.

    Regresa los k más parecidos como lista de (similitud, fragmento),
    del más parecido al menos.
    """
    vector_pregunta = vectorizar(pregunta)
    puntuados = []
    for fragmento in indice:
        similitud = coseno(vector_pregunta, fragmento["vector"])
        puntuados.append((similitud, fragmento))

    # Ordenar por la similitud (el elemento [0] de cada pareja), de mayor a menor.
    puntuados.sort(key=lambda pareja: pareja[0], reverse=True)
    return puntuados[:k]


def armar_prompt(pregunta, resultados):
    """4. PROMPT: instrucciones + fragmentos encontrados + la pregunta.

    Mismo formato que lab7/src/rag_engine.py. La instrucción "si no está ahí,
    di que no lo sabes" es lo que evita que el LLM invente respuestas.
    """
    bloques = []
    for _similitud, fragmento in resultados:   # el "_" indica que aquí no usamos la similitud
        bloques.append(f"Fuente: {fragmento['fuente']}\n{fragmento['texto']}")
    contexto = "\n\n".join(bloques)

    return (
        "Responde usando ÚNICAMENTE el CONTEXTO. Si la respuesta no está ahí, "
        "di que no lo sabes.\n\n"
        f"CONTEXTO:\n{contexto}\n\nPREGUNTA: {pregunta}"
    )


def responder(pregunta, indice):
    """Hace todo el flujo RAG para una pregunta e imprime cada paso."""
    print("=" * 70)
    print(f"PREGUNTA: {pregunta}")
    resultados = buscar(pregunta, indice)
    print("\nFragmentos recuperados:")
    for similitud, fragmento in resultados:
        print(f"  {similitud:4.2f}  [{fragmento['fuente']}] {fragmento['texto'][:60]}...")

    mejor_similitud = resultados[0][0]
    if mejor_similitud < UMBRAL:
        print("\n-> Ningún fragmento se parece lo suficiente: el agente diría 'no lo sé'")
        print("   en vez de inventar (así se reducen las alucinaciones).")
        return

    # Un fragmento con similitud 0 no aporta nada; no lo mandamos al LLM.
    utiles = []
    for similitud, fragmento in resultados:
        if similitud > 0:
            utiles.append((similitud, fragmento))

    print("\n5. Esto es lo que se le mandaría al LLM (Gemini en lab7):")
    print("-" * 70)
    print(armar_prompt(pregunta, utiles))
    print("-" * 70)


def main():
    indice = construir_indice()
    print(f"Índice: {len(DOCUMENTOS)} documentos -> {len(indice)} fragmentos\n")

    # Si escribiste una pregunta al correr el script, solo responde esa.
    # sys.argv = ["mini_rag.py", "¿a", "qué", "hora", "abren?"] -> juntamos todo menos el nombre.
    if len(sys.argv) > 1:
        responder(" ".join(sys.argv[1:]), indice)
        return

    for pregunta in [
        "¿A qué horas abren los sábados?",
        "¿Cuánto cuesta un latte?",
        "¿Puedo llevar a mi perro?",          # "perro" no aparece; el doc dice "mascotas"
        "¿Quién es el dueño de la cafetería?",  # la respuesta no está en ningún documento
    ]:
        responder(pregunta, indice)

    print("\nFíjate en '¿Puedo llevar a mi perro?': el conteo de palabras no sabe")
    print("que perro ~ mascota. Con embeddings de verdad (lab7) sí lo encontraría.")


if __name__ == "__main__":
    main()
