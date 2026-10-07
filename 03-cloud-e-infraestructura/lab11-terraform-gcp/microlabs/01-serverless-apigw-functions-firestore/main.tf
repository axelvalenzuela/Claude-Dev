# Micro lab 01 (GCP) - API serverless: API Gateway + Cloud Run functions + Firestore
# Capas: API key + cuota (gateway) -> ID token del SA del gateway (la función NO es pública)
#        -> validación en código -> IAM condicionado a una sola base de Firestore

data "google_project" "this" {}

locals {
  name = "lab11-${var.environment}-api"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "01-serverless-apigw-functions-firestore"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "apigateway.googleapis.com",
    "servicemanagement.googleapis.com",
    "servicecontrol.googleapis.com",
    "apikeys.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "firestore.googleapis.com",
  ]
}

# ---------------- Datos ----------------
resource "google_firestore_database" "items" {
  name                              = "${local.name}-items"
  location_id                       = var.region
  type                              = "FIRESTORE_NATIVE"
  point_in_time_recovery_enablement = "POINT_IN_TIME_RECOVERY_ENABLED"
  delete_protection_state           = "DELETE_PROTECTION_DISABLED"
  deletion_policy                   = "DELETE"
  depends_on                        = [module.services]
}

# ---------------- Identidades ----------------
module "function_sa" {
  source       = "../../modules/service-account"
  project_id   = var.project_id
  account_id   = "${local.name}-fn"
  display_name = "Runtime de la función items"
  depends_on   = [module.services]
}

# Acceso SOLO a esta base de Firestore (IAM condition sobre el nombre del recurso)
resource "google_project_iam_member" "function_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = module.function_sa.member

  condition {
    title      = "solo-${google_firestore_database.items.name}"
    expression = "resource.name.startsWith(\"projects/${var.project_id}/databases/${google_firestore_database.items.name}\")"
  }
}

module "gateway_sa" {
  source       = "../../modules/service-account"
  project_id   = var.project_id
  account_id   = "${local.name}-gw"
  display_name = "API Gateway -> backend"
  depends_on   = [module.services]
}

# ---------------- Cómputo ----------------
module "source_bucket" {
  source          = "../../modules/gcs-secure-bucket"
  project_id      = var.project_id
  name            = "${var.project_id}-${local.name}-src"
  location        = var.region
  expiration_days = 30
  depends_on      = [module.services]
}

module "items_fn" {
  source                = "../../modules/cloud-function"
  project_id            = var.project_id
  region                = var.region
  name                  = "${local.name}-items"
  description           = "CRUD de items"
  source_dir            = "${path.module}/src/items"
  source_bucket         = module.source_bucket.name
  build_service_account = var.build_service_account
  service_account_email = module.function_sa.email
  max_instances         = var.max_instances
  environment = {
    FIRESTORE_DATABASE = google_firestore_database.items.name
    FAULT_INJECTION    = var.enable_fault_injection ? "enabled" : "disabled"
  }
  # Solo el gateway puede invocar la función
  invoker_members = [module.gateway_sa.member]
}

# ---------------- API Gateway ----------------
resource "google_api_gateway_api" "this" {
  provider   = google-beta
  api_id     = local.name
  depends_on = [module.services]
}

resource "google_api_gateway_api_config" "this" {
  provider             = google-beta
  api                  = google_api_gateway_api.this.api_id
  api_config_id_prefix = "${local.name}-"

  openapi_documents {
    document {
      path = "openapi.yaml"
      contents = base64encode(templatefile("${path.module}/openapi.yaml.tpl", {
        api_id           = local.name
        function_uri     = module.items_fn.uri
        quota_per_minute = var.quota_per_minute
      }))
    }
  }

  gateway_config {
    backend_config {
      google_service_account = module.gateway_sa.email
    }
  }

  # Un cambio de contrato crea un config nuevo antes de retirar el anterior (sin caída)
  lifecycle {
    create_before_destroy = true
  }
}

resource "google_api_gateway_gateway" "this" {
  provider   = google-beta
  gateway_id = local.name
  region     = var.region
  api_config = google_api_gateway_api_config.this.id
}

# El servicio administrado del API debe habilitarse para aceptar API keys
resource "google_project_service" "managed_api" {
  project            = var.project_id
  service            = google_api_gateway_api.this.managed_service
  disable_on_destroy = false
}

resource "google_apikeys_key" "client" {
  name         = "${local.name}-client-demo"
  display_name = "Cliente demo lab11"

  restrictions {
    api_targets {
      service = google_api_gateway_api.this.managed_service
    }
  }

  depends_on = [google_project_service.managed_api]
}
