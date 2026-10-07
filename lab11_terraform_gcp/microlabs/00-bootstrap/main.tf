# Micro lab 00 (GCP) - Bootstrap de la plataforma
# 1. APIs base, bucket de estado de Terraform (GCS, versionado, bloqueo nativo)
# 2. Workload Identity Federation para GitLab: SIN llaves JSON de service accounts
# 3. SA plan (lectura) / SA apply (solo rama main) / SA de Cloud Build para los labs
# 4. Artifact Registry y presupuesto con alertas

data "google_project" "this" {}

locals {
  name = "lab11-${var.environment}"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "00-bootstrap"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "billingbudgets.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
  ]
}

# ---------------------------------------------------------------------------
# 1. Estado remoto: GCS bloquea el estado de forma nativa (sin tabla de locks)
# ---------------------------------------------------------------------------
module "state_bucket" {
  source                  = "../../modules/gcs-secure-bucket"
  project_id              = var.project_id
  name                    = "${var.project_id}-lab11-tfstate"
  location                = var.region
  force_destroy           = false
  noncurrent_version_days = 90
  soft_delete_days        = 30
  labels                  = local.common_labels
  depends_on              = [module.services]
}

# ---------------------------------------------------------------------------
# 2. Workload Identity Federation (GitLab OIDC -> STS -> impersonación de SA)
# ---------------------------------------------------------------------------
resource "google_iam_workload_identity_pool" "gitlab" {
  workload_identity_pool_id = "${local.name}-gitlab"
  display_name              = "GitLab CI (lab11)"
  description               = "Identidades de pipelines de GitLab"
  depends_on                = [module.services]
}

resource "google_iam_workload_identity_pool_provider" "gitlab" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.gitlab.workload_identity_pool_id
  workload_identity_pool_provider_id = "gitlab"
  display_name                       = "gitlab.com"

  # Claims del id_token de GitLab -> atributos de Google
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.project_id" = "assertion.project_id"
    "attribute.ref"        = "assertion.ref"
    "attribute.deploy_ref" = "assertion.project_id + ':' + assertion.ref_type + ':' + assertion.ref"
    "attribute.protected"  = "assertion.ref_protected"
  }

  # Solo tokens de ESTE proyecto de GitLab pueden intercambiarse
  attribute_condition = "assertion.project_path == '${var.gitlab_project_path}'"

  oidc {
    issuer_uri        = var.gitlab_url
    allowed_audiences = [var.gitlab_url]
  }
}

module "plan_sa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "${local.name}-tf-plan"
  display_name  = "Terraform plan (lectura)"
  project_roles = ["roles/viewer", "roles/iam.securityReviewer"]
  depends_on    = [module.services]
}

module "apply_sa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "${local.name}-tf-apply"
  display_name  = "Terraform apply (rama protegida)"
  project_roles = var.apply_roles
  depends_on    = [module.services]
}

# Cualquier rama/MR del proyecto puede hacer plan
resource "google_service_account_iam_member" "plan_wif" {
  service_account_id = module.plan_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.gitlab.name}/attribute.project_id/${var.gitlab_project_id}"
}

# Solo la rama por defecto puede aplicar
resource "google_service_account_iam_member" "apply_wif" {
  service_account_id = module.apply_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.gitlab.name}/attribute.deploy_ref/${var.gitlab_project_id}:branch:${var.gitlab_default_branch}"
}

# Ambos necesitan leer/escribir el estado y su archivo de lock
resource "google_storage_bucket_iam_member" "state" {
  for_each = {
    plan  = module.plan_sa.member
    apply = module.apply_sa.member
  }
  bucket = module.state_bucket.name
  role   = "roles/storage.objectAdmin"
  member = each.value
}

# ---------------------------------------------------------------------------
# 3. SA de Cloud Build para construir Cloud Run functions de los labs
# ---------------------------------------------------------------------------
module "builder_sa" {
  source       = "../../modules/service-account"
  project_id   = var.project_id
  account_id   = "${local.name}-builder"
  display_name = "Cloud Build para Cloud Run functions"
  project_roles = [
    "roles/cloudbuild.builds.builder",
    "roles/logging.logWriter",
    "roles/artifactregistry.writer",
    "roles/storage.objectViewer",
  ]
  depends_on = [module.services]
}

# El SA de apply debe poder "actuar como" el builder al desplegar funciones
resource "google_service_account_iam_member" "apply_uses_builder" {
  service_account_id = module.builder_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = module.apply_sa.member
}

# ---------------------------------------------------------------------------
# 4. Artifact Registry + presupuesto
# ---------------------------------------------------------------------------
resource "google_artifact_registry_repository" "containers" {
  repository_id = "lab11"
  location      = var.region
  format        = "DOCKER"
  description   = "Imágenes de los micro labs"

  cleanup_policies {
    id     = "keep-last-10"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }

  cleanup_policies {
    id     = "delete-untagged"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "604800s"
    }
  }

  depends_on = [module.services]
}

resource "google_monitoring_notification_channel" "email" {
  count        = var.alert_email == null ? 0 : 1
  display_name = "lab11 alertas"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
  depends_on = [module.services]
}

resource "google_billing_budget" "monthly" {
  count           = var.billing_account == null ? 0 : 1
  billing_account = var.billing_account
  display_name    = "${local.name}-monthly"

  budget_filter {
    projects = ["projects/${data.google_project.this.number}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget)
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 0.8
  }
  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "FORECASTED_SPEND"
  }

  dynamic "all_updates_rule" {
    for_each = var.alert_email == null ? [] : [1]
    content {
      monitoring_notification_channels = [google_monitoring_notification_channel.email[0].id]
      disable_default_iam_recipients   = false
    }
  }
}
