variable "project_id" {
  type = string
}

variable "account_id" {
  type        = string
  description = "Short id for the service account (<= 30 chars). Becomes <account_id>@<project_id>.iam.gserviceaccount.com."
}

variable "display_name" {
  type    = string
  default = ""
}

variable "roles" {
  type        = list(string)
  description = "Project-level IAM roles granted to this identity. Keep this list as short as the workload actually needs — this module grants exactly these roles and nothing else."
  default     = []
}

resource "google_service_account" "this" {
  project      = var.project_id
  account_id   = var.account_id
  display_name = var.display_name != "" ? var.display_name : var.account_id
}

resource "google_project_iam_member" "roles" {
  for_each = toset(var.roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.this.email}"
}

output "email" {
  value = google_service_account.this.email
}

output "name" {
  value = google_service_account.this.name
}
