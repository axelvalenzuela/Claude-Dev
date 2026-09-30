"""Micro lab 13 — RAG con embeddings de Vertex AI sobre conocimiento de migración.

Es el micro lab 09 (parte 1) pero con las piezas reales:
    vectorizar = modelo de embeddings (gemini-embedding-001)
    generar    = Gemini

  PASO #1: partir los documentos de conocimiento/ en fragmentos
  PASO #2: embeber los fragmentos UNA vez (RETRIEVAL_DOCUMENT) y guardar el índice
  PASO #3: embeber la pregunta (RETRIEVAL_QUERY) y buscar top-k por coseno
  PASO #4: armar el prompt con CONTEXTO y generar la respuesta
  EXTRA:  comparar contra búsqueda por palabras para ver por qué los embeddings ganan

Correr (desde parte2_gcp/):
    python 13_embeddings_rag/rag_sas.py
    python 13_embeddings_rag/rag_sas.py "¿cómo convierto un IF THEN de SAS?"
"""
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comun import llm  # noqa: E402
from comun.config import config  # noqa: E402

AQUI = Path(__file__).resolve().parent
TOP_K = 3
UMBRAL = 0.35   # por debajo de esto, mejor "no sé". Se calibra con preguntas reales.

SISTEMA = (
    "Eres un experto en migración de SAS a Python y BigQuery. Responde usando ÚNICAMENTE "
    "el CONTEXTO. Si la respuesta no está en el CONTEXTO, di que no lo sabes. "
    "Cita la fuente entre corchetes."
)


# PASO #1 — cada párrafo es un fragmento; le pegamos el título para no perder contexto
def fragmentar() -> list[dict]:
    fragmentos = []
    for ruta in sorted((AQUI / "conocimiento").glob("*.md")):
        lineas = [linea.strip() for linea in ruta.read_text(encoding="utf-8").splitlines() if linea.strip()]
        titulo = lineas[0].lstrip("# ")
        for parrafo in lineas[1:]:
            fragmentos.append({"fuente": ruta.name, "texto": f"{titulo}. {parrafo}"})
    return fragmentos


# PASO #2 — el índice se guarda en disco: embeber cuesta, no hay que repetirlo
def construir_indice() -> list[dict]:
    archivo = AQUI / f".indice_{config.modo}_{config.modelo_embeddings}.json"
    if archivo.exists():
        return json.loads(archivo.read_text(encoding="utf-8"))
    fragmentos = fragmentar()
    vectores = llm.embeber([f["texto"] for f in fragmentos], tipo="RETRIEVAL_DOCUMENT")
    for f, v in zip(fragmentos, vectores):
        f["vector"] = v
    archivo.write_text(json.dumps(fragmentos), encoding="utf-8")
    return fragmentos


def coseno(a, b) -> float:
    punto = sum(x * y for x, y in zip(a, b))
    norma = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return punto / norma if norma else 0.0


# PASO #3 — buscar
def buscar(pregunta: str, indice: list[dict], k: int = TOP_K) -> list[tuple[float, dict]]:
    v = llm.embeber([pregunta], tipo="RETRIEVAL_QUERY")[0]
    return sorted(((coseno(v, f["vector"]), f) for f in indice), key=lambda x: x[0], reverse=True)[:k]


def buscar_por_palabras(pregunta: str, indice: list[dict]) -> tuple[float, dict]:
    """La técnica del micro lab 09, para comparar."""
    palabras = lambda t: Counter(re.findall(r"\w{3,}", t.lower()))  # noqa: E731
    vp = palabras(pregunta)
    puntuados = []
    for f in indice:
        vf = palabras(f["texto"])
        punto = sum(vp[p] * vf[p] for p in vp)
        norma = math.sqrt(sum(x * x for x in vp.values())) * math.sqrt(sum(x * x for x in vf.values()))
        puntuados.append((punto / norma if norma else 0.0, f))
    return max(puntuados, key=lambda x: x[0])


# PASO #4 — generar con contexto
def responder(pregunta: str, indice: list[dict]) -> None:
    print("=" * 72)
    print(f"PREGUNTA: {pregunta}\n")
    resultados = buscar(pregunta, indice)
    sim_p, frag_p = buscar_por_palabras(pregunta, indice)
    print(f"  por palabras   -> {sim_p:.2f} [{frag_p['fuente']}]")
    print(f"  por embeddings -> {resultados[0][0]:.2f} [{resultados[0][1]['fuente']}]")

    relevantes = [(s, f) for s, f in resultados if s >= UMBRAL]
    if not relevantes:
        print("\nRESPUESTA: No lo sé: nada en la base de conocimiento se parece lo suficiente.")
        return
    contexto = "\n\n".join(f"Fuente: {f['fuente']}\n{f['texto']}" for _, f in relevantes)
    prompt = f"CONTEXTO:\n{contexto}\n\nPREGUNTA: {pregunta}"
    r = llm.generar(prompt, rol="rag", sistema=SISTEMA)
    print(f"\nRESPUESTA: {r.texto}")
    print(f"(fuentes: {sorted({f['fuente'] for _, f in relevantes})}, costo ${r.costo_usd:.6f})")


def main():
    indice = construir_indice()
    print(f"Índice: {len(indice)} fragmentos, vectores de {len(indice[0]['vector'])} dimensiones "
          f"(modo {config.modo})\n")
    preguntas = sys.argv[1:] and [" ".join(sys.argv[1:])] or [
        "¿Cómo quito registros repetidos de una tabla?",   # el doc dice "duplicados", no "repetidos"
        "¿Cómo saco el promedio por grupo?",               # el doc dice "media"/MEAN
        "¿Qué servicio uso para calendarizar procesos?",
        "¿Cuánto cuesta una licencia de SAS?",             # no está en la base -> debe decir "no sé"
    ]
    for p in preguntas:
        responder(p, indice)


if __name__ == "__main__":
    main()
