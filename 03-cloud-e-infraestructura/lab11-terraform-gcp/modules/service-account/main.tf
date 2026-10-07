# Módulo: service account dedicada con roles de proyecto explícitos (mínimo privilegio).
# Nunca se crean llaves JSON: las cargas usan la SA adjunta o Workload Identity.

resource "google_service_account" "this" {
  project      = var.project_id
  account_id   = var.account_id
  display_name = var.display_name
  description  = var.description
}

resource "google_project_iam_member" "roles" {
  for_each = toset(var.project_roles)
  project  = var.project_id
  role     = each.value
  member   = google_service_account.this.member
}
