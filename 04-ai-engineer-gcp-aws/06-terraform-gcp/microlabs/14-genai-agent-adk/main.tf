# Micro lab 14 (GCP) - Agente con Google ADK (Agent Development Kit) + herramientas sobre Firestore
#   Cloud Run function privada -> ADK Runner -> Gemini decide qué herramienta usar
#   Herramientas: consultar_pedido (Firestore), politica_devoluciones, crear_ticket (escritura)
#   El mismo agente se puede desplegar en Vertex AI Agent Engine con `adk deploy agent_engine` (ver README).

locals {
  name = "aie-${var.environment}-agent"

  common_labels = {
    project     = "aie"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "14-genai-agent-adk"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "aiplatform.googleapis.com",
    "firestore.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
  ]
}

# ---------------- Datos del negocio que consultan las herramientas ----------------
resource "google_firestore_database" "store" {
  name                    = "${local.name}-store"
  location_id             = var.region
  type                    = "FIRESTORE_NATIVE"
  delete_protection_state = "DELETE_PROTECTION_DISABLED"
  deletion_policy         = "DELETE"
  depends_on              = [module.services]
}

# Pedidos de ejemplo (cámbialos en var.sample_orders)
resource "google_firestore_document" "orders" {
  for_each    = var.sample_orders
  database    = google_firestore_database.store.name
  collection  = "pedidos"
  document_id = each.key
  fields = jsonencode({
    estado           = { stringValue = each.value.estado }
    total_mxn        = { doubleValue = each.value.total_mxn }
    entrega_estimada = { stringValue = each.value.entrega_estimada }
    categoria        = { stringValue = each.value.categoria }
  })
}

# ---------------- Identidad del agente ----------------
module "agent_sa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "${local.name}-fn"
  display_name  = "Runtime del agente ADK"
  project_roles = ["roles/aiplatform.user"]
  depends_on    = [module.services]
}

# Las herramientas leen pedidos y crean tickets SOLO en esta base
resource "google_project_iam_member" "agent_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = module.agent_sa.member

  condition {
    title      = "solo-${google_firestore_database.store.name}"
    expression = "resource.name.startsWith(\"projects/${var.project_id}/databases/${google_firestore_database.store.name}\")"
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

module "agent_fn" {
  source                = "../../modules/cloud-function"
  project_id            = var.project_id
  region                = var.region
  name                  = "${local.name}-api"
  description           = "Agente de soporte ADK"
  source_dir            = "${path.module}/src/agent"
  source_bucket         = module.source_bucket.name
  build_service_account = var.build_service_account
  service_account_email = module.agent_sa.email
  memory                = "1Gi"
  cpu                   = "1"
  concurrency           = 4
  timeout_seconds       = 120
  max_instances         = 3
  invoker_members       = var.invoker_members
  environment = {
    GOOGLE_GENAI_USE_VERTEXAI = "TRUE"
    GOOGLE_CLOUD_PROJECT      = var.project_id
    GOOGLE_CLOUD_LOCATION     = var.vertex_location
    MODEL                     = var.model
    FIRESTORE_DATABASE        = google_firestore_database.store.name
  }
}
