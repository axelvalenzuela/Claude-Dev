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

PALABRAS_VACIAS = set(
    "el la los las de del en y a un una es se con por para que al lo su tu "
    "mi sin cada son esta esta hay como cual cuanto cuanta cuando donde "
    "puedo puede tienen tiene hoy".split()
)
TOP_K = 2
UMBRAL = 0.15   # si el mejor fragmento se parece menos que esto, mejor decir "no sé"


def normalizar(texto):
    """minúsculas, sin acentos, sin signos, sin palabras vacías."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return [p for p in re.findall(r"[a-z0-9]+", texto) if p not in PALABRAS_VACIAS]


def partir(texto, tamano=14, traslape=4):
    """1. CHUNKING: ventanas de palabras que se enciman un poco (igual que
    lab7/src/chunking.py, pero con fragmentos mucho más chicos)."""
    palabras = texto.split()
    paso = tamano - traslape
    return [" ".join(palabras[i:i + tamano]) for i in range(0, max(len(palabras) - traslape, 1), paso)]


def vectorizar(texto):
    """2. VECTORES: aquí un simple conteo de palabras. En lab7 esto lo hace
    el modelo text-embedding-005 de Vertex AI."""
    return Counter(normalizar(texto))


def coseno(a, b):
    punto = sum(a[p] * b[p] for p in a)
    norma = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return punto / norma if norma else 0.0


def construir_indice():
    indice = []
    for fuente, texto in DOCUMENTOS.items():
        for fragmento in partir(texto):
            indice.append({"fuente": fuente, "texto": fragmento, "vector": vectorizar(fragmento)})
    return indice


def buscar(pregunta, indice, k=TOP_K):
    """3. RETRIEVAL: comparar la pregunta contra TODOS los fragmentos."""
    v = vectorizar(pregunta)
    puntuados = sorted(((coseno(v, f["vector"]), f) for f in indice), key=lambda x: x[0], reverse=True)
    return puntuados[:k]


def armar_prompt(pregunta, resultados):
    """4. PROMPT: mismo formato que lab7/src/rag_engine.py."""
    contexto = "\n\n".join(f"Fuente: {f['fuente']}\n{f['texto']}" for _, f in resultados)
    return (
        "Responde usando ÚNICAMENTE el CONTEXTO. Si la respuesta no está ahí, "
        "di que no lo sabes.\n\n"
        f"CONTEXTO:\n{contexto}\n\nPREGUNTA: {pregunta}"
    )


def responder(pregunta, indice):
    print("=" * 70)
    print(f"PREGUNTA: {pregunta}")
    resultados = buscar(pregunta, indice)
    print("\nFragmentos recuperados:")
    for sim, f in resultados:
        print(f"  {sim:4.2f}  [{f['fuente']}] {f['texto'][:60]}...")

    if resultados[0][0] < UMBRAL:
        print("\n-> Ningún fragmento se parece lo suficiente: el agente diría 'no lo sé'")
        print("   en vez de inventar (así se reducen las alucinaciones).")
        return

    # Un fragmento con similitud 0 no aporta nada; no lo mandamos al LLM.
    resultados = [(sim, f) for sim, f in resultados if sim > 0]

    print("\n5. Esto es lo que se le mandaría al LLM (Gemini en lab7):")
    print("-" * 70)
    print(armar_prompt(pregunta, resultados))
    print("-" * 70)


def main():
    indice = construir_indice()
    print(f"Índice: {len(DOCUMENTOS)} documentos -> {len(indice)} fragmentos\n")

    if len(sys.argv) > 1:
        responder(" ".join(sys.argv[1:]), indice)
        return

    for pregunta in (
        "¿A qué horas abren los sábados?",
        "¿Cuánto cuesta un latte?",
        "¿Puedo llevar a mi perro?",          # "perro" no aparece; el doc dice "mascotas"
        "¿Quién es el dueño de la cafetería?",  # la respuesta no está en ningún documento
    ):
        responder(pregunta, indice)

    print("\nFíjate en '¿Puedo llevar a mi perro?': el conteo de palabras no sabe")
    print("que perro ~ mascota. Con embeddings de verdad (lab7) sí lo encontraría.")


if __name__ == "__main__":
    main()
