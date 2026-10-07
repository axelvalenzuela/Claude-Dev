"""05 · Embeddings y búsqueda semántica (la "R" de RAG).

Concepto: un embedding convierte texto en un vector; significados parecidos quedan cerca.
Usa task_type distinto para documentos y para la pregunta: mejora la recuperación.

    python 05_gemini_embeddings_search.py
"""

from common import cosine, embed

docs = [
    "Para restablecer tu contraseña entra a Configuración > Seguridad.",
    "Las facturas se envían por correo el día 5 de cada mes.",
    "El plan Pro incluye 100 GB de almacenamiento y soporte 24/7.",
    "Puedes cancelar tu suscripción en cualquier momento sin penalización.",
]
doc_vectors = [embed(d, "RETRIEVAL_DOCUMENT") for d in docs]

query = "olvidé mi clave, ¿cómo la cambio?"   # ninguna palabra coincide con el documento correcto
q = embed(query, "RETRIEVAL_QUERY")

print(f"Consulta: {query}\n")
for doc, score in sorted(zip(docs, (cosine(q, v) for v in doc_vectors)), key=lambda x: -x[1]):
    print(f"{score:.3f}  {doc}")
