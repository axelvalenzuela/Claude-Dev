"""
Lab 9 - Embeddings y busqueda semantica (la base de RAG)

Un embedding convierte un texto en un vector de numeros; textos con significado parecido
quedan cerca. task_type le dice al modelo para que se usara el vector:
    RETRIEVAL_DOCUMENT -> los documentos que vas a guardar/indexar.
    RETRIEVAL_QUERY    -> la pregunta del usuario.
    (otros: SEMANTIC_SIMILARITY, CLASSIFICATION, CLUSTERING, QUESTION_ANSWERING...)
output_dimensionality reduce el tamano del vector (3072 -> 768) para ahorrar almacenamiento.
En produccion los vectores se guardan en Vertex AI Vector Search, BigQuery o AlloyDB.
"""

import math

from google.genai import types

from comun import MODELO_EMBEDDINGS, crear_cliente

client = crear_cliente()

DOCUMENTOS = [
    "Peter Parker gets his powers from the bite of a radioactive spider.",
    "Tony Stark builds the Iron Man armor while held captive in a cave.",
    "Wakanda hides its vibranium technology from the rest of the world.",
    "Doctor Strange learns the mystic arts in Kamar-Taj after a car accident.",
]


def embedding(texto: str, tarea: str) -> list[float]:
    # Un texto por llamada: en Vertex AI gemini-embedding-001 acepta una entrada por peticion.
    resultado = client.models.embed_content(
        model=MODELO_EMBEDDINGS,
        contents=texto,
        config=types.EmbedContentConfig(task_type=tarea, output_dimensionality=768),
    )
    return resultado.embeddings[0].values


def similitud_coseno(a: list[float], b: list[float]) -> float:
    producto = sum(x * y for x, y in zip(a, b))
    return producto / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


indice = [(doc, embedding(doc, "RETRIEVAL_DOCUMENT")) for doc in DOCUMENTOS]
print(f"Vectores de {len(indice[0][1])} dimensiones para {len(indice)} documentos.\n")

for pregunta in ["Which hero is a genius engineer?", "Where does the hidden African kingdom keep its metal?"]:
    vector = embedding(pregunta, "RETRIEVAL_QUERY")
    ranking = sorted(indice, key=lambda item: similitud_coseno(vector, item[1]), reverse=True)
    print(f"Pregunta: {pregunta}")
    for doc, vec in ranking[:2]:
        print(f"  {similitud_coseno(vector, vec):.3f}  {doc}")
    print()
