# Baseline que se aplica a CADA proyecto creado por la fábrica (equivalente al template de StackSets):
# APIs, sin red default, auditoría de acceso a datos, presupuesto y grupo de operadores.

resource "google_project" "this" {
  name                = var.name
  project_id          = var.project_id
  folder_id           = var.folder_id
  billing_account     = var.billing_account
  auto_create_network = false # sin VPC "default" con reglas permisivas
  deletion_policy     = var.deletion_policy
  labels              = var.labels
}

resource "google_project_service" "this" {
  for_each           = toset(var.services)
  project            = google_project.this.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_iam_audit_config" "data_access" {
  project = google_project.this.project_id
  service = "allServices"

  audit_log_config {
    log_type = "ADMIN_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

resource "google_project_iam_member" "operators" {
  for_each = toset(var.operator_members)
  project  = google_project.this.project_id
  role     = "roles/editor"
  member   = each.value
}

resource "google_billing_budget" "this" {
  billing_account = var.billing_account
  display_name    = "${var.project_id}-budget"

  budget_filter {
    projects = ["projects/${google_project.this.number}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget)
    }
  }

  threshold_rules {
    threshold_percent = 0.8
  }
  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "FORECASTED_SPEND"
  }
}
