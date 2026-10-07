# 17 — BigQuery: SQL migrado, dry run, reconciliación y búsqueda vectorial

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #22 de 26** · [← #21 Evaluación y quality gate](../16_evaluacion/README.md) · [#23 Cloud Functions + Storage →](../18_cloud_functions_storage/README.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

**Qué aprendes:** convertir SAS a BigQuery SQL con IA y validarlo sin gastar; usar
BigQuery como base vectorial; y la infraestructura como código que lo crea.

## Conceptos

- **Dataset / tabla**: el dataset agrupa tablas y define ubicación (`US`) y permisos. Los crea
  Terraform ([infra/bigquery.tf](../../infra/bigquery.tf)), no el código: la infraestructura es
  revisable, versionada y repetible.
- **Cobro on-demand**: por bytes **leídos** (6.25 USD/TiB; 1 TiB gratis al mes; mínimo 10 MB por consulta).
  BigQuery es columnar: leer 2 columnas cuesta menos que `SELECT *`.
- **Dry run**: valida el SQL y dice cuántos bytes leería **sin ejecutarlo ni cobrar**. Es la
  validación perfecta para SQL generado por un LLM.
- **Carga (load job) vs streaming**: cargar archivos es gratis; `insert_rows_json` (streaming) se cobra.
- **Particionamiento** (`auditoria_llm` por día) y **clustering**: consultar "ayer" solo lee ayer.
- **`VECTOR_SEARCH`**: búsqueda por similitud sobre una columna `ARRAY<FLOAT64>`. RAG sin servidores extra.

| Archivo | Qué hace |
|---|---|
| [bq.py](bq.py) | Ayudante: cargar CSV, dry run, consultar. En simulado usa SQLite |
| [sas_a_bigquery.py](sas_a_bigquery.py) | SAS → SQL con Gemini → dry run → ejecutar → reconciliar |
| [rag_en_bigquery.py](rag_en_bigquery.py) | Carga los embeddings del lab 13 y busca con `VECTOR_SEARCH` (solo real) |

## Para la entrevista

- *"¿Cómo validas SQL generado?"* → dry run (sintaxis + costo) → ejecutar sobre datos de prueba →
  reconciliar contra SAS. Si falla, el error vuelve al LLM.
- *"¿Cómo controlas el costo de BigQuery?"* → dry run, particiones, clustering, no `SELECT *`,
  `maximum_bytes_billed` en consultas, y revisar `INFORMATION_SCHEMA.JOBS` por bytes facturados.

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
