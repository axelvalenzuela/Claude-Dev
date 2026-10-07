locals {
  etiquetas = {
    proyecto = "lab8-migracion-sas"
    entorno  = "lab"
  }
}

resource "google_bigquery_dataset" "migracion" {
  dataset_id                 = var.dataset
  location                   = var.ubicacion_bigquery
  description                = "Lab 8: datos de ejemplo, resultados y auditoría de la migración SAS -> Python"
  delete_contents_on_destroy = true # es un lab; en producción déjalo en false
  labels                     = local.etiquetas

  depends_on = [google_project_service.apis]
}

# Datos de entrada (equivale a raw.ventas de SAS). Lo carga 17_bigquery/sas_a_bigquery.py.
# Nota: en producción el dinero va en NUMERIC (exacto); aquí FLOAT64 para comparar fácil con pandas.
resource "google_bigquery_table" "ventas" {
  dataset_id          = google_bigquery_dataset.migracion.dataset_id
  table_id            = "ventas"
  deletion_protection = false
  labels              = local.etiquetas

  schema = jsonencode([
    { name = "id", type = "INT64", mode = "REQUIRED" },
    { name = "fecha", type = "DATE", mode = "REQUIRED" },
    { name = "region", type = "STRING", mode = "REQUIRED" },
    { name = "estado", type = "STRING", mode = "REQUIRED" },
    { name = "monto", type = "FLOAT64", mode = "REQUIRED" },
  ])
}

# Resultado de la migración (equivale a resumen_ventas de SAS).
resource "google_bigquery_table" "resumen_ventas" {
  dataset_id          = google_bigquery_dataset.migracion.dataset_id
  table_id            = "resumen_ventas"
  deletion_protection = false
  labels              = local.etiquetas

  schema = jsonencode([
    { name = "region", type = "STRING" },
    { name = "categoria", type = "STRING" },
    { name = "num_ventas", type = "INT64" },
    { name = "total", type = "FLOAT64" },
  ])
}

# Estado de cada programa migrado por el DAG de Composer (lab 20).
resource "google_bigquery_table" "reporte_migracion" {
  dataset_id          = google_bigquery_dataset.migracion.dataset_id
  table_id            = "reporte_migracion"
  deletion_protection = false
  labels              = local.etiquetas

  schema = jsonencode([
    { name = "programa", type = "STRING" },
    { name = "estado", type = "STRING" },
    { name = "intentos", type = "INT64" },
    { name = "costo_usd", type = "FLOAT64" },
    { name = "fecha", type = "TIMESTAMP" },
  ])
}

# Una fila por llamada al LLM (lab 21). Particionada por día: consultar "ayer" solo lee (y cobra) ayer.
resource "google_bigquery_table" "auditoria_llm" {
  dataset_id          = google_bigquery_dataset.migracion.dataset_id
  table_id            = "auditoria_llm"
  deletion_protection = false
  labels              = local.etiquetas

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
  clustering = ["rol", "modelo"]

  schema = jsonencode([
    { name = "timestamp", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "modo", type = "STRING" },
    { name = "tipo", type = "STRING" },
    { name = "rol", type = "STRING" },
    { name = "modelo", type = "STRING" },
    { name = "tokens_entrada", type = "INT64" },
    { name = "tokens_salida", type = "INT64" },
    { name = "costo_usd", type = "FLOAT64" },
    { name = "latencia_s", type = "FLOAT64" },
  ])
}

# Base de conocimiento vectorial para RAG con VECTOR_SEARCH (17_bigquery/rag_en_bigquery.py).
resource "google_bigquery_table" "conocimiento" {
  dataset_id          = google_bigquery_dataset.migracion.dataset_id
  table_id            = "conocimiento"
  deletion_protection = false
  labels              = local.etiquetas

  schema = jsonencode([
    { name = "fuente", type = "STRING" },
    { name = "texto", type = "STRING" },
    { name = "embedding", type = "FLOAT64", mode = "REPEATED" },
  ])
}
