# Micro lab 12 (GCP) - RAG con BigQuery Vector Search + Gemini
#   Documentos -> chunks -> ML.GENERATE_EMBEDDING (modelo remoto de Vertex AI vía BigQuery connection)
#   Pregunta -> embedding de la pregunta -> VECTOR_SEARCH (coseno) -> top-k chunks -> Gemini responde con citas
#   Todo el "vector store" vive en BigQuery: sin infraestructura extra, SQL estándar, IAM y costos de BigQuery.

locals {
  name    = "aie-${var.environment}-rag"
  dataset = replace("${local.name}_kb", "-", "_")

  common_labels = {
    project     = "aie"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "12-genai-rag-bigquery-vector"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "bigquery.googleapis.com",
    "bigqueryconnection.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
  ]
}

# ---------------- Base de conocimiento en BigQuery ----------------
resource "google_bigquery_dataset" "kb" {
  dataset_id                 = local.dataset
  location                   = var.bq_location
  description                = "Base de conocimiento vectorial para RAG"
  delete_contents_on_destroy = true
  depends_on                 = [module.services]
}

# Chunks con su embedding (ARRAY<FLOAT64>) listo para VECTOR_SEARCH
resource "google_bigquery_table" "chunks" {
  dataset_id          = google_bigquery_dataset.kb.dataset_id
  table_id            = "chunks"
  deletion_protection = false
  clustering          = ["source"]

  schema = jsonencode([
    { name = "chunk_id", type = "STRING", mode = "REQUIRED" },
    { name = "source", type = "STRING", mode = "REQUIRED", description = "archivo de origen (se cita en la respuesta)" },
    { name = "content", type = "STRING", mode = "REQUIRED" },
    { name = "embedding", type = "FLOAT64", mode = "REPEATED" },
    { name = "ingested_at", type = "TIMESTAMP", mode = "NULLABLE" },
  ])
}

# ---------------- Modelo remoto de embeddings (BigQuery ML -> Vertex AI) ----------------
resource "google_bigquery_connection" "vertex" {
  connection_id = "${local.name}-vertex"
  location      = var.bq_location
  description   = "BigQuery -> Vertex AI (embeddings)"
  cloud_resource {}
  depends_on = [module.services]
}

# La identidad de la conexión llama a Vertex AI
resource "google_project_iam_member" "connection_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_bigquery_connection.vertex.cloud_resource[0].service_account_id}"
}

resource "random_id" "model_job" {
  byte_length = 4
  keepers = {
    endpoint = var.embedding_endpoint # cambia el endpoint => se recrea el modelo
  }
}

# DDL de BigQuery ML ejecutado como job de Terraform
resource "google_bigquery_job" "embedding_model" {
  job_id   = "create_embedding_model_${random_id.model_job.hex}"
  location = var.bq_location

  query {
    query              = "CREATE OR REPLACE MODEL `${var.project_id}.${local.dataset}.embedding_model` REMOTE WITH CONNECTION `${var.project_id}.${lower(var.bq_location)}.${google_bigquery_connection.vertex.connection_id}` OPTIONS (ENDPOINT = '${var.embedding_endpoint}')"
    use_legacy_sql     = false
    create_disposition = ""
    write_disposition  = ""
  }

  depends_on = [google_project_iam_member.connection_vertex, google_bigquery_dataset.kb]
}

# ---------------- Servicio de preguntas ----------------
module "rag_sa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "${local.name}-fn"
  display_name  = "Runtime del servicio RAG"
  project_roles = ["roles/bigquery.jobUser", "roles/aiplatform.user"]
  depends_on    = [module.services]
}

resource "google_bigquery_dataset_iam_member" "rag_reads" {
  dataset_id = google_bigquery_dataset.kb.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = module.rag_sa.member
}

# Usar el modelo remoto requiere permiso sobre la conexión
resource "google_bigquery_connection_iam_member" "rag_uses_connection" {
  project       = var.project_id
  location      = var.bq_location
  connection_id = google_bigquery_connection.vertex.connection_id
  role          = "roles/bigquery.connectionUser"
  member        = module.rag_sa.member
}

module "source_bucket" {
  source          = "../../modules/gcs-secure-bucket"
  project_id      = var.project_id
  name            = "${var.project_id}-${local.name}-src"
  location        = var.region
  expiration_days = 30
  depends_on      = [module.services]
}

module "rag_fn" {
  source                = "../../modules/cloud-function"
  project_id            = var.project_id
  region                = var.region
  name                  = "${local.name}-ask"
  description           = "Pregunta -> VECTOR_SEARCH -> Gemini con citas"
  source_dir            = "${path.module}/src/ask"
  source_bucket         = module.source_bucket.name
  build_service_account = var.build_service_account
  service_account_email = module.rag_sa.email
  memory                = "512Mi"
  cpu                   = "1"
  concurrency           = 8
  timeout_seconds       = 60
  max_instances         = 3
  invoker_members       = var.invoker_members
  environment = {
    GOOGLE_CLOUD_PROJECT = var.project_id
    VERTEX_LOCATION      = var.vertex_location
    MODEL                = var.model
    DATASET              = local.dataset
    TOP_K                = tostring(var.top_k)
    MAX_DISTANCE         = tostring(var.max_distance)
  }
}
