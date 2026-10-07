# Micro lab 03 (GCP) - Chatbot de IA generativa con Vertex AI Gemini
#   Cloud Run function PRIVADA (solo identidades con run.invoker) -> Vertex AI (google-genai)
#   Firestore para historial con política TTL nativa · guardrails en capas · métricas de tokens en logs

locals {
  name = "lab11-${var.environment}-chat"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "03-vertex-ai-chatbot"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "aiplatform.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "firestore.googleapis.com",
    "logging.googleapis.com",
  ]
}

# ---------------- Historial ----------------
resource "google_firestore_database" "history" {
  name                    = "${local.name}-history"
  location_id             = var.region
  type                    = "FIRESTORE_NATIVE"
  delete_protection_state = "DELETE_PROTECTION_DISABLED"
  deletion_policy         = "DELETE"
  depends_on              = [module.services]
}

# Índice compuesto para "mensajes de la sesión ordenados por tiempo"
resource "google_firestore_index" "session_ts" {
  database   = google_firestore_database.history.name
  collection = "messages"

  fields {
    field_path = "session_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "ts"
    order      = "DESCENDING"
  }
}

# TTL: Firestore borra los documentos cuando expires_at queda en el pasado
resource "google_firestore_field" "ttl" {
  database   = google_firestore_database.history.name
  collection = "messages"
  field      = "expires_at"

  ttl_config {}

  index_config {}
}

# ---------------- Identidad ----------------
module "chat_sa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "${local.name}-fn"
  display_name  = "Runtime del chatbot"
  project_roles = ["roles/aiplatform.user"]
  depends_on    = [module.services]
}

resource "google_project_iam_member" "chat_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = module.chat_sa.member

  condition {
    title      = "solo-${google_firestore_database.history.name}"
    expression = "resource.name.startsWith(\"projects/${var.project_id}/databases/${google_firestore_database.history.name}\")"
  }
}

# ---------------- Función ----------------
module "source_bucket" {
  source          = "../../modules/gcs-secure-bucket"
  project_id      = var.project_id
  name            = "${var.project_id}-${local.name}-src"
  location        = var.region
  expiration_days = 30
  depends_on      = [module.services]
}

module "chat_fn" {
  source                = "../../modules/cloud-function"
  project_id            = var.project_id
  region                = var.region
  name                  = "${local.name}-api"
  description           = "Chatbot con Vertex AI Gemini"
  source_dir            = "${path.module}/src/chat"
  source_bucket         = module.source_bucket.name
  build_service_account = var.build_service_account
  service_account_email = module.chat_sa.email
  memory                = "512Mi"
  cpu                   = "1"
  concurrency           = 8
  timeout_seconds       = 60
  max_instances         = var.max_instances
  invoker_members       = var.invoker_members
  environment = {
    GOOGLE_CLOUD_PROJECT = var.project_id
    VERTEX_LOCATION      = var.vertex_location
    MODEL                = var.model
    FIRESTORE_DATABASE   = google_firestore_database.history.name
    SYSTEM_INSTRUCTION   = var.system_instruction
    HISTORY_TURNS        = tostring(var.history_turns)
    MAX_OUTPUT_TOKENS    = tostring(var.max_output_tokens)
    BLOCKED_TOPICS       = join(",", var.blocked_topics)
    TTL_HOURS            = "24"
  }
}

# ---------------- Observabilidad de costo ----------------
resource "google_logging_metric" "output_tokens" {
  name   = "${local.name}/output_tokens"
  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${module.chat_fn.service_name}\" AND jsonPayload.output_tokens>0"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "DISTRIBUTION"
    unit        = "1"
  }

  value_extractor = "EXTRACT(jsonPayload.output_tokens)"

  bucket_options {
    exponential_buckets {
      num_finite_buckets = 20
      growth_factor      = 2
      scale              = 1
    }
  }
}

resource "google_logging_metric" "guardrail_blocks" {
  name   = "${local.name}/guardrail_blocks"
  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${module.chat_fn.service_name}\" AND jsonPayload.msg=\"guardrail de entrada\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}
