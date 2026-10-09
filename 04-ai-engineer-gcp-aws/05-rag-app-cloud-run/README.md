# RAG sobre Vertex AI Gemini, con página de chat

Un **Agente de Consulta** mínimo: una página web de chat, un backend en
Python (FastAPI) desplegable en **Cloud Run**, y un pipeline RAG
(*Retrieval-Augmented Generation*) que responde preguntas basándose en un
puñado de documentos propios en vez de solo en lo que Gemini ya sabe.

```
Navegador → FastAPI (Cloud Run) → índice vectorial local → Vertex AI (embeddings)
                                                          → Vertex AI (Gemini, genera la respuesta)
```

El caso de uso es ficticio pero deliberadamente cercano a un escenario
real de migración de sistemas legacy a GCP con IA (SAS → Python/BigQuery):
los documentos en [data/docs/](data/docs/) describen el "Programa Helios"
de una empresa inventada, "Acme Analytics". El agente responde preguntas
sobre ese programa citando de qué documento sacó cada dato — y admite
cuando no lo sabe, en vez de inventar.

## Por qué este ejercicio

Sirve como base práctica y pequeña de las piezas que aparecen en casi
cualquier puesto de "AI Engineer" orientado a GCP: Vertex AI + Gemini,
RAG, una base vectorial (aquí, la versión simple; en producción sería
Vertex AI Vector Search o pgvector), y un servicio desplegado en Cloud
Run. No implementa multi-agente ni orquestación (eso queda para un lab
futuro) — es, a propósito, el escalón más básico y completo posible: se
puede correr localmente, entender cada línea, y desplegarlo de verdad.

## Contenido

| Archivo | Qué contiene |
|---|---|
| [CONCEPTOS.md](CONCEPTOS.md) | Qué es RAG y por qué, embeddings vs. generación, cómo funciona la búsqueda por similitud, y hacia dónde crece esto (Vertex AI Vector Search, multi-agente). |
| [INSTRUCCIONES.md](INSTRUCCIONES.md) | Paso a paso: cuenta GCP, credenciales, correr localmente, probar RAG on/off, desplegar a Cloud Run manualmente, limpiar recursos, troubleshooting. |
| [src/](src/) | Todo el código Python, documentado línea por línea (ver tabla abajo). |
| [web/](web/) | La página de chat: HTML + CSS + JS plano, sin frameworks ni build step. |
| [data/docs/](data/docs/) | La base de conocimiento ficticia que el RAG consulta. |
| [tests/](tests/) | Pruebas de la lógica que no depende de GCP (chunking, similitud de coseno). |
| [infra/](infra/) | Terraform opcional para desplegar el Cloud Run como IaC (ver su propio README). |

## Estructura de archivos

```
05-rag-app-cloud-run/
├── README.md                  este archivo
├── CONCEPTOS.md                RAG, embeddings, vectores — la teoría
├── INSTRUCCIONES.md            guía paso a paso (local + Cloud Run)
├── requirements.txt
├── .env.example                 variables de entorno a copiar a .env
├── Dockerfile                   imagen para Cloud Run
├── src/
│   ├── config.py                lee variables de entorno (proyecto, región, modelos)
│   ├── chunking.py              parte los documentos en fragmentos (sin dependencias de GCP)
│   ├── gemini_client.py         único archivo que llama a Vertex AI (embeddings + Gemini)
│   ├── vector_store.py          índice vectorial en memoria (NumPy) + guardar/cargar en disco
│   ├── ingest.py                orquesta: lee docs -> chunking -> embeddings -> guarda índice
│   ├── rag_engine.py             retrieve + arma el prompt + genera la respuesta
│   └── main.py                   servidor FastAPI: sirve la página y /api/chat
├── web/
│   ├── index.html                página de chat (con interruptor "usar RAG")
│   ├── app.js                    llama a /api/chat por fetch()
│   └── style.css
├── data/
│   ├── docs/                     5 documentos .md (la base de conocimiento del "Programa Helios")
│   └── index/                    generado al ingerir — no se versiona (.gitignore)
├── tests/
│   ├── test_chunking.py           prueba chunking sin credenciales GCP
│   └── test_vector_store.py       prueba la búsqueda por similitud sin credenciales GCP
└── infra/                        Terraform opcional (Cloud Run + IAM + APIs)
```

## Quickstart (ver [INSTRUCCIONES.md](INSTRUCCIONES.md) para el detalle)

```bash
cd 05-rag-app-cloud-run
python -m venv .venv && source .venv/bin/activate   # o .venv\Scripts\activate en Windows
pip install -r requirements.txt

cp .env.example .env            # y editar GCP_PROJECT_ID
gcloud auth application-default login

python -m src.ingest            # construye el índice vectorial (opcional: la app lo hace sola)
uvicorn src.main:app --reload --port 8080
# abrir http://localhost:8080
```

## Estado de validación

| Pieza | Estado |
|---|---|
| `tests/test_chunking.py`, `tests/test_vector_store.py` | Lógica verificada a mano (ver comentarios en el código); **no se ejecutaron con pytest** — no hay Python instalado en el entorno donde se generó este lab. Correlas tú con `pytest tests/ -v`. |
| Llamadas reales a Vertex AI (`embed_content`, `generate_content`) | No probadas — requieren un proyecto GCP con facturación y credenciales, que este entorno no tiene. La forma de las llamadas sigue la API pública documentada del SDK `google-genai`, pero **confirma los nombres de modelo** (`EMBEDDING_MODEL`, `GENERATION_MODEL` en `.env`) contra Vertex AI Model Garden antes de depender de ellos: los ids de modelo cambian con el tiempo. |
| `infra/` (Terraform) | No ejecutado (`terraform` no está instalado en este entorno). Revisar antes de aplicar. |
| `Dockerfile` | No construido/probado (no hay Docker corriendo en este entorno). |

## Nota importante

Este es un ejercicio de aprendizaje con una base de conocimiento
**ficticia** (Acme Analytics / Programa Helios no existen). El patrón —
chunking, embeddings, búsqueda por similitud, prompt con contexto,
generación — es el mismo que usarías con documentos reales; solo cambia
qué hay en `data/docs/`.
