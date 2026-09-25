# Composition root: no bare `google_*` resources here (except the module
# calls themselves) — every actual resource lives inside modules/*, the
# same pattern lab6/terraform uses for its AWS modules.

module "apis" {
  source = "./modules/apis"

  project_id = var.project_id
}

module "service_account" {
  source = "./modules/service_account"

  project_id   = var.project_id
  account_id   = "${var.service_name}-sa"
  display_name = "Runtime SA for ${var.service_name} (Vertex AI RAG demo)"

  # The only permission this app's runtime identity needs: call Vertex AI
  # (embed_content, generate_content). No BigQuery, no Storage, no IAM.
  roles = ["roles/aiplatform.user"]

  depends_on = [module.apis]
}

module "cloud_run" {
  source = "./modules/cloud_run"

  project_id             = var.project_id
  region                 = var.region
  service_name           = var.service_name
  container_image        = var.container_image
  service_account_email  = module.service_account.email
  allow_unauthenticated  = var.allow_unauthenticated

  env_vars = {
    GCP_PROJECT_ID   = var.project_id
    GCP_LOCATION     = var.region
    EMBEDDING_MODEL  = var.embedding_model
    GENERATION_MODEL = var.generation_model
  }

  depends_on = [module.apis]
}
