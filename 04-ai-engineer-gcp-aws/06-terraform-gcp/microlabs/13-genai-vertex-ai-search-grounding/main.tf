# Micro lab 13 (GCP) - RAG administrado: Vertex AI Search (AI Applications) + grounding de Gemini
#   GCS (docs) -> data store (layout parser + chunking) -> search engine (Enterprise + LLM add-on)
#   Modo "gemini": Gemini con la herramienta Retrieval(VertexAISearch) -> respuesta + grounding_metadata
#   Modo "search": Search API con resumen y citas generados por el motor
#   Compáralo con el micro lab 12 (RAG "hecho a mano" en BigQuery): aquí Google hace parsing, chunking, ranking y citas.

locals {
  name = "aie-${var.environment}-search"

  common_labels = {
    project     = "aie"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "13-genai-vertex-ai-search-grounding"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "discoveryengine.googleapis.com",
    "aiplatform.googleapis.com",
    "storage.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
  ]
}

# ---------------- Documentos fuente ----------------
module "docs" {
  source        = "../../modules/gcs-secure-bucket"
  project_id    = var.project_id
  name          = "${var.project_id}-${local.name}-docs"
  location      = var.region
  force_destroy = true
  labels        = local.common_labels
  depends_on    = [module.services]
}

resource "google_storage_bucket_object" "docs" {
  for_each       = fileset("${path.module}/data", "*.txt")
  bucket         = module.docs.name
  name           = "docs/${each.value}"
  source         = "${path.module}/data/${each.value}"
  content_type   = "text/plain"
  source_md5hash = filemd5("${path.module}/data/${each.value}")
}

# Discovery Engine lee el bucket con su agente de servicio
data "google_project" "this" {}

resource "google_storage_bucket_iam_member" "discovery_reads_docs" {
  bucket = module.docs.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
}

# ---------------- Data store + motor de búsqueda ----------------
resource "google_discovery_engine_data_store" "docs" {
  location          = var.search_location
  data_store_id     = "${local.name}-docs"
  display_name      = "aie documentos"
  industry_vertical = "GENERIC"
  content_config    = "CONTENT_REQUIRED" # documentos no estructurados (PDF, HTML, TXT, DOCX)
  solution_types    = ["SOLUTION_TYPE_SEARCH"]

  # Parsing por layout + chunking: requisito para respuestas con citas a nivel de fragmento
  document_processing_config {
    default_parsing_config {
      layout_parsing_config {}
    }
    chunking_config {
      layout_based_chunking_config {
        chunk_size                = var.chunk_size
        include_ancestor_headings = true
      }
    }
  }

  depends_on = [module.services]
}

resource "google_discovery_engine_search_engine" "docs" {
  engine_id         = "${local.name}-engine"
  collection_id     = "default_collection"
  location          = var.search_location
  display_name      = "aie buscador"
  industry_vertical = "GENERIC"
  data_store_ids    = [google_discovery_engine_data_store.docs.data_store_id]

  search_engine_config {
    search_tier    = "SEARCH_TIER_ENTERPRISE"
    search_add_ons = ["SEARCH_ADD_ON_LLM"] # resúmenes y respuestas generativas
  }

  common_config {
    company_name = var.company_name
  }
}

# ---------------- Servicio de respuestas ----------------
module "answer_sa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "${local.name}-fn"
  display_name  = "Runtime del servicio de respuestas"
  project_roles = ["roles/discoveryengine.viewer", "roles/aiplatform.user"]
  depends_on    = [module.services]
}

module "source_bucket" {
  source          = "../../modules/gcs-secure-bucket"
  project_id      = var.project_id
  name            = "${var.project_id}-${local.name}-src"
  location        = var.region
  expiration_days = 30
  depends_on      = [module.services]
}

module "answer_fn" {
  source                = "../../modules/cloud-function"
  project_id            = var.project_id
  region                = var.region
  name                  = "${local.name}-answer"
  description           = "Grounding con Vertex AI Search"
  source_dir            = "${path.module}/src/answer"
  source_bucket         = module.source_bucket.name
  build_service_account = var.build_service_account
  service_account_email = module.answer_sa.email
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
    SEARCH_LOCATION      = var.search_location
    DATA_STORE_ID        = google_discovery_engine_data_store.docs.data_store_id
    ENGINE_ID            = google_discovery_engine_search_engine.docs.engine_id
  }
}
