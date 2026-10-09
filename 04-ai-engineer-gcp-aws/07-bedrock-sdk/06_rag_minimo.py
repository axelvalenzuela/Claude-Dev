"""06 · RAG mínimo: recuperar contexto + generar una respuesta con citas.

Concepto: el modelo no conoce TUS documentos. RAG = (1) buscar los fragmentos relevantes
con embeddings, (2) pasarlos en el prompt, (3) pedir que responda SOLO con ellos y cite la fuente.

    python 06_rag_minimo.py "¿cuánto tarda un reembolso?"
"""

import sys

from common import ask, cosine, embed

knowledge = {
    "politica-reembolsos.md": "Los reembolsos se procesan en 5 a 7 días hábiles después de aprobar la solicitud.",
    "envios.md": "Los envíos nacionales tardan 2 a 4 días; a Baja California 3 a 5 días.",
    "garantia.md": "La garantía cubre defectos de fábrica durante 12 meses con ticket de compra.",
}
vectors = {name: embed(text) for name, text in knowledge.items()}

question = sys.argv[1] if len(sys.argv) > 1 else "¿cuánto tarda un reembolso?"
q = embed(question)
top = sorted(vectors, key=lambda n: -cosine(q, vectors[n]))[:2]
context = "\n".join(f"[{n}] {knowledge[n]}" for n in top)

answer, usage = ask(
    f"Contexto:\n{context}\n\nPregunta: {question}",
    system="Responde SOLO con el contexto. Cita la fuente entre corchetes. Si no está en el contexto, di 'No lo sé'.",
)
print(f"Fuentes recuperadas: {top}\n\n{answer}\n\nTokens: {usage}")
