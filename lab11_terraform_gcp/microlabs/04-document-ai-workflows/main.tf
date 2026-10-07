# Micro lab 04 (GCP) - Pipeline de IA para documentos, orquestado y SIN funciones propias
#   GCS (incoming/) -> Eventarc (object.finalized) -> Cloud Workflows
#     -> Vision OCR (imágenes) / lectura directa (.txt)
#     -> Parallel[ Natural Language entidades | Vertex AI Gemini resumen ]
#     -> BigQuery (insertAll) ; errores -> log ERROR + alerta

data "google_project" "this" {}

locals {
  name = "lab11-${var.environment}-docai"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "04-document-ai-workflows"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "workflows.googleapis.com",
    "workflowexecutions.googleapis.com",
    "eventarc.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "vision.googleapis.com",
    "language.googleapis.com",
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
  ]
}

# ---------------- Entrada ----------------
module "documents" {
  source          = "../../modules/gcs-secure-bucket"
  project_id      = var.project_id
  name            = "${var.project_id}-${local.name}-docs"
  location        = var.region
  expiration_days = var.document_retention_days
  labels          = local.common_labels
  depends_on      = [module.services]
}

# ---------------- Salida ----------------
resource "google_bigquery_dataset" "results" {
  dataset_id                 = replace("${local.name}_results", "-", "_")
  location                   = var.region
  delete_contents_on_destroy = true
  depends_on                 = [module.services]
}

resource "google_bigquery_table" "documents" {
  dataset_id          = google_bigquery_dataset.results.dataset_id
  table_id            = "documents"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "processed_at"
  }

  schema = jsonencode([
    { name = "document_id", type = "STRING", mode = "REQUIRED" },
    { name = "bucket", type = "STRING", mode = "NULLABLE" },
    { name = "summary", type = "STRING", mode = "NULLABLE" },
    { name = "entities", type = "JSON", mode = "NULLABLE" },
    { name = "processed_at", type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "execution", type = "STRING", mode = "NULLABLE" },
  ])
}

# ---------------- Identidad del workflow (mínimo privilegio) ----------------
module "workflow_sa" {
  source       = "../../modules/service-account"
  project_id   = var.project_id
  account_id   = "${local.name}-wf"
  display_name = "Workflow de documentos"
  project_roles = [
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/serviceusage.serviceUsageConsumer", # Vision y Natural Language
  ]
  depends_on = [module.services]
}

resource "google_storage_bucket_iam_member" "workflow_reads_docs" {
  bucket = module.documents.name
  role   = "roles/storage.objectViewer"
  member = module.workflow_sa.member
}

resource "google_bigquery_dataset_iam_member" "workflow_writes" {
  dataset_id = google_bigquery_dataset.results.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = module.workflow_sa.member
}

resource "google_workflows_workflow" "pipeline" {
  name            = "${local.name}-pipeline"
  region          = var.region
  description     = "OCR/lectura -> entidades + resumen -> BigQuery"
  service_account = module.workflow_sa.id
  call_log_level  = "LOG_ERRORS_ONLY" # no registra el contenido de los documentos
  source_contents = file("${path.module}/workflow.yaml")

  user_env_vars = {
    MODEL           = var.model
    VERTEX_LOCATION = var.vertex_location
    LANGUAGE        = var.language
    DATASET         = google_bigquery_dataset.results.dataset_id
    TABLE           = google_bigquery_table.documents.table_id
  }

  deletion_protection = false
  depends_on          = [module.services]
}

# ---------------- Disparador: Eventarc ----------------
module "trigger_sa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "${local.name}-trg"
  display_name  = "Eventarc -> Workflows"
  project_roles = ["roles/workflows.invoker", "roles/eventarc.eventReceiver"]
  depends_on    = [module.services]
}

# El agente de Cloud Storage publica los eventos en Pub/Sub (transporte de Eventarc)
data "google_storage_project_service_account" "gcs" {
  depends_on = [module.services]
}

resource "google_project_iam_member" "gcs_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = data.google_storage_project_service_account.gcs.member
}

resource "google_eventarc_trigger" "new_document" {
  name            = "${local.name}-new-document"
  location        = var.region
  service_account = module.trigger_sa.email

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  matching_criteria {
    attribute = "bucket"
    value     = module.documents.name
  }

  destination {
    workflow = google_workflows_workflow.pipeline.id
  }

  depends_on = [google_project_iam_member.gcs_pubsub_publisher]
}

# ---------------- Alerta de ejecuciones fallidas ----------------
resource "google_monitoring_alert_policy" "failed" {
  display_name = "${local.name} ejecuciones fallidas"
  combiner     = "OR"

  conditions {
    display_name = "Workflow FAILED"
    condition_threshold {
      filter          = "resource.type = \"workflows.googleapis.com/Workflow\" AND resource.labels.workflow_id = \"${google_workflows_workflow.pipeline.name}\" AND metric.type = \"workflows.googleapis.com/finished_execution_count\" AND metric.labels.status = \"FAILED\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = var.notification_channels
}
