# Micro lab 16 (GCP) - Ciclo de mejora de modelos: datos -> fine-tuning -> batch -> evaluación
#   Terraform crea el bucket de datasets/resultados y los permisos del agente de Vertex AI.
#   Los scripts (Python + google-genai) generan el dataset, lanzan el SFT, la batch prediction y la evaluación.

data "google_project" "this" {}

locals {
  name = "aie-${var.environment}-tuning"

  common_labels = {
    project     = "aie"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "16-genai-tuning-batch-eval"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services   = ["aiplatform.googleapis.com", "storage.googleapis.com"]
}

# datasets/ (train, validation, batch input) y outputs/ (batch, evaluaciones)
module "ml_bucket" {
  source                  = "../../modules/gcs-secure-bucket"
  project_id              = var.project_id
  name                    = "${var.project_id}-${local.name}"
  location                = var.region # mismo lugar que los jobs de Vertex AI
  noncurrent_version_days = 7
  expiration_days         = var.data_retention_days
  labels                  = local.common_labels
  depends_on              = [module.services]
}

# El agente de servicio de Vertex AI lee los datasets y escribe los resultados de batch
resource "google_project_service_identity" "vertex" {
  provider   = google-beta
  project    = var.project_id
  service    = "aiplatform.googleapis.com"
  depends_on = [module.services]
}

resource "google_storage_bucket_iam_member" "vertex_agent" {
  bucket = module.ml_bucket.name
  role   = "roles/storage.objectAdmin"
  member = google_project_service_identity.vertex.member
}

# Alerta de costo: los jobs de tuning se cobran por tokens de entrenamiento
resource "google_monitoring_alert_policy" "tuning_job_failed" {
  display_name = "${local.name} tuning job fallido"
  combiner     = "OR"

  conditions {
    display_name = "Error en jobs de tuning"
    condition_matched_log {
      filter = "resource.type=\"aiplatform.googleapis.com/TuningJob\" AND severity>=ERROR"
    }
  }

  alert_strategy {
    notification_rate_limit {
      period = "3600s"
    }
  }

  notification_channels = var.notification_channels
}
