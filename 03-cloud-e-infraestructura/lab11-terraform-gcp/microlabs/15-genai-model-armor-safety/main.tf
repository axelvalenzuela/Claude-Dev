# Micro lab 15 (GCP) - Seguridad de LLMs con Model Armor
#   Template: prompt injection + jailbreak, filtros RAI (odio, acoso, sexual, peligroso),
#             Sensitive Data Protection (tarjetas, credenciales...) y URLs maliciosas
#   Función "safe-chat": sanitize_user_prompt -> Gemini -> sanitize_model_response
#   El mismo template sirve para CUALQUIER modelo (Gemini, open models, otros proveedores).

locals {
  name = "lab11-${var.environment}-armor"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "15-genai-model-armor-safety"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "modelarmor.googleapis.com",
    "dlp.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
  ]
}

resource "google_model_armor_template" "this" {
  location    = var.region
  template_id = "${local.name}-template"

  filter_config {
    rai_settings {
      dynamic "rai_filters" {
        for_each = toset(["HATE_SPEECH", "HARASSMENT", "SEXUALLY_EXPLICIT", "DANGEROUS"])
        content {
          filter_type      = rai_filters.value
          confidence_level = var.rai_confidence
        }
      }
    }

    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = var.injection_confidence
    }

    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }

    sdp_settings {
      basic_config {
        filter_enforcement = "ENABLED" # tarjetas, credenciales, identificadores comunes
      }
    }
  }

  template_metadata {
    log_template_operations = true
    log_sanitize_operations = true # deja rastro de cada evaluación en Cloud Logging
  }

  labels     = local.common_labels
  depends_on = [module.services]
}

module "chat_sa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "${local.name}-fn"
  display_name  = "Runtime de safe-chat"
  project_roles = ["roles/aiplatform.user", "roles/modelarmor.user"]
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

module "chat_fn" {
  source                = "../../modules/cloud-function"
  project_id            = var.project_id
  region                = var.region
  name                  = "${local.name}-chat"
  description           = "Gemini protegido con Model Armor"
  source_dir            = "${path.module}/src/chat"
  source_bucket         = module.source_bucket.name
  build_service_account = var.build_service_account
  service_account_email = module.chat_sa.email
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
    ARMOR_LOCATION       = var.region
    TEMPLATE             = google_model_armor_template.this.id
  }
}
