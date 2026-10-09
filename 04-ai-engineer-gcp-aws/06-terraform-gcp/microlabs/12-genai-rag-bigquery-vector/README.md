# Micro lab 12 (GCP · GenAI): RAG con BigQuery Vector Search + Gemini

> **Objetivo:** Construir RAG **de punta a punta y entendiendo cada pieza**: chunking, embeddings con un modelo remoto de Vertex AI dentro de BigQuery, búsqueda vectorial con `VECTOR_SEARCH`, umbral de relevancia y respuesta con citas.

<!-- despliegue -->
## Despliegue paso a paso (desde cero)

> Si es tu primera vez, sigue antes la guía general [DESPLIEGUE.md](../../DESPLIEGUE.md) (herramientas, credenciales y micro lab 00).

**Tiempo de apply:** ~6 min · **Costo si queda encendido:** Por uso (BigQuery + tokens)

**Prerrequisitos**

- Micro lab 00 (`build_service_account`)
- Python 3.11+ con `pip install google-cloud-bigquery` para `ingest.py`

**1. Prepara las variables**

```bash
cd 06-terraform-gcp
cp microlabs/12-genai-rag-bigquery-vector/terraform.tfvars.example microlabs/12-genai-rag-bigquery-vector/terraform.tfvars
```

Edita como mínimo:

| Variable | Valor |
|---|---|
| `project_id` | tu proyecto |
| `owner` | label |
| `invoker_members` | `["user:tu@correo"]` |
| `build_service_account` | output del micro lab 00 |

**2. Despliega**

```bash
export TF_STATE_BUCKET=<output tf_state_bucket del micro lab 00>
bash scripts/lab.sh init  12-genai-rag-bigquery-vector
bash scripts/lab.sh plan  12-genai-rag-bigquery-vector   # revisa qué se crea
bash scripts/lab.sh apply 12-genai-rag-bigquery-vector
```

**3. Después del apply**

- Ingresa la base de conocimiento: `python microlabs/12-genai-rag-bigquery-vector/scripts/ingest.py`
- Pregunta: `curl -X POST $(terraform -chdir=microlabs/12-genai-rag-bigquery-vector output -raw ask_url) -H "Authorization: Bearer $(gcloud auth print-identity-token)" -H 'Content-Type: application/json' -d '{"question":"¿Cuántos días de vacaciones tengo?"}'`

**4. Verifica**

```bash
bash scripts/lab.sh test 12-genai-rag-bigquery-vector   # debe terminar en SMOKE TEST OK
```

**5. Destruye al terminar**

```bash
bash scripts/lab.sh destroy 12-genai-rag-bigquery-vector
```
<!-- despliegue -->

<!-- modificar -->
## Qué modificar en los templates

| Archivo / bloque | Qué cambiar | Cuándo |
|---|---|---|
| `terraform.tfvars` | Valores de tu entorno: proyecto/cuenta, `owner`, correos, regiones | Siempre, antes del primer apply |
| data/*.md | Tu base de conocimiento (o `ingest.py --docs <carpeta>`) | Siempre |
| scripts/ingest.py → `chunk(max_chars, overlap_chars)` | Estrategia de chunking | Si las respuestas pierden contexto |
| variables.tf → `embedding_endpoint` | Modelo de embeddings (re-ingesta obligatoria al cambiarlo) | Idioma o calidad |
| variables.tf → `top_k`, `max_distance` | Cuánto contexto y qué tan relevante | Afinar precisión vs cobertura |
| src/ask/main.py → `SYSTEM` | Reglas de respuesta y formato de citas | Siempre |

> Regla: cambia **variables** (`terraform.tfvars`) para configurar; cambia **templates y código** para extender. Después de cualquier cambio: `bash scripts/lab.sh plan <lab>` para revisar el impacto antes de aplicar.
<!-- modificar -->
## Arquitectura

```
Documentos (data/*.md)
   │ scripts/ingest.py: chunking por párrafos (900 caracteres, overlap 150)
   ▼
BigQuery: chunks_staging ──ML.GENERATE_EMBEDDING(RETRIEVAL_DOCUMENT)──► kb.chunks (content, source, embedding ARRAY<FLOAT64>)
                                 │ modelo remoto embedding_model (CONNECTION → Vertex AI text-multilingual-embedding-002)
Usuario ──ID token──► Cloud Run function ask
   1. ML.GENERATE_EMBEDDING(pregunta, RETRIEVAL_QUERY)  ┐ una sola consulta SQL
   2. VECTOR_SEARCH(top_k=4, COSINE) + filtro distance ≤ 0.6 ┘
   3. Gemini: "responde SOLO con el CONTEXTO y cita [fuente]"  → answer + sources + tokens
```

## Conceptos clave (nivel senior)

| Concepto | Lo que debes saber explicar |
|---|---|
| Chunking | Dividir documentos en fragmentos. Muy chicos pierden contexto; muy grandes diluyen la relevancia. El overlap evita cortar ideas. |
| Embeddings y task_type | `RETRIEVAL_DOCUMENT` para indexar y `RETRIEVAL_QUERY` para preguntar: modelos asimétricos que mejoran la recuperación. |
| Distancia coseno | 0 = idéntico, 2 = opuesto. `max_distance` descarta contexto irrelevante y es la primera defensa contra alucinaciones. |
| Brute force vs índice | Sin índice, `VECTOR_SEARCH` compara contra todo (exacto, bien hasta ~100 k filas). `CREATE VECTOR INDEX ... OPTIONS(index_type='IVF')` da ANN a escala (requiere ≥ 5,000 filas). |
| Modelo remoto de BigQuery ML | BigQuery llama a Vertex AI con la identidad de la CONNECTION: los datos no salen a otro sistema y todo es SQL. |
| Evaluar RAG | Separa recuperación (¿trajo el chunk correcto? recall@k) de generación (¿fiel al contexto? groundedness). |
| Re-ingesta | Cambiar el modelo de embeddings invalida todos los vectores: hay que regenerarlos. |

## Recursos de Terraform y código

| Recurso / archivo | Propósito |
|---|---|
| `google_bigquery_connection.vertex` + IAM | Conexión CLOUD_RESOURCE con `aiplatform.user` |
| `google_bigquery_job.embedding_model` | DDL `CREATE MODEL ... REMOTE WITH CONNECTION` ejecutado por Terraform |
| `google_bigquery_table.chunks` | Vector store: `embedding FLOAT64 REPEATED`, clustering por `source` |
| `module.rag_fn` + `src/ask/main.py` | Retrieval parametrizado + generación con citas |
| `scripts/ingest.py` | Chunking + `ML.GENERATE_EMBEDDING` + re-ingesta idempotente |

## Comandos útiles

```bash
bq query --use_legacy_sql=false 'SELECT source, COUNT(*) FROM `<proyecto>.<dataset>.chunks` GROUP BY source'
bq query --use_legacy_sql=false 'CREATE VECTOR INDEX idx ON `<dataset>.chunks`(embedding) OPTIONS(index_type="IVF", distance_type="COSINE")'
bq ls --models <dataset>
bq show --connection <proyecto>.us.<connection_id>
```

## Prueba automatizada (`scripts/smoke-test.sh`)

Ingresa la base si está vacía; 403 sin token; responde "12 días" citando `vacaciones.md`; encuentra "60 dólares" aunque se pregunte por "comida" (semántica); ante una pregunta fuera de dominio responde "No tengo esa información".

## Troubleshooting

| Síntoma | Causa y solución |
|---|---|
| `ML.GENERATE_EMBEDDING` falla con permisos | La SA de la conexión necesita `aiplatform.user` (incluido); espera 1-2 min a que propague IAM. |
| `User does not have bigquery.connections.use` | La SA de la función necesita `connectionUser` sobre la conexión (incluido). |
| Respuestas "No tengo esa información" para todo | `max_distance` demasiado bajo o la tabla está vacía; corre `ingest.py`. |

## Costo

BigQuery por bytes escaneados + embeddings por carácter + tokens de Gemini (centavos para el lab).
