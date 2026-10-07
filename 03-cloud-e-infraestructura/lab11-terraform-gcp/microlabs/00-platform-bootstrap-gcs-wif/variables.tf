variable "project_id" {
  description = "Proyecto de GCP donde viven los labs (debe tener facturación activa)."
  type        = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "owner" {
  description = "Etiqueta owner (minúsculas, números, guiones o guion bajo)."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9_-]{1,63}$", var.owner))
    error_message = "owner debe ser un valor de label válido: [a-z0-9_-], máx. 63."
  }
}

variable "cost_center" {
  type    = string
  default = "training"
}

variable "gitlab_url" {
  type    = string
  default = "https://gitlab.com"
}

variable "gitlab_project_path" {
  description = "grupo/subgrupo/proyecto en GitLab."
  type        = string
}

variable "gitlab_project_id" {
  description = "ID numérico del proyecto de GitLab (Settings > General)."
  type        = string
}

variable "gitlab_default_branch" {
  type    = string
  default = "main"
}

variable "apply_roles" {
  description = "Roles del SA de apply. Ajusta a lo mínimo que usen tus labs."
  type        = list(string)
  default = [
    "roles/editor",
    "roles/resourcemanager.projectIamAdmin",
    "roles/iam.serviceAccountAdmin",
    "roles/iam.serviceAccountUser",
    "roles/cloudkms.admin",
    "roles/secretmanager.admin",
    "roles/run.admin",
    "roles/cloudfunctions.admin",
    "roles/storage.admin",
    "roles/bigquery.admin",
    "roles/monitoring.admin",
    "roles/logging.admin",
    "roles/compute.securityAdmin",
    "roles/iam.denyAdmin",
  ]
}

variable "billing_account" {
  description = "ID de la cuenta de facturación (XXXXXX-XXXXXX-XXXXXX) para el presupuesto. null = sin presupuesto."
  type        = string
  default     = null
}

variable "monthly_budget" {
  type    = number
  default = 50
}

variable "alert_email" {
  type    = string
  default = null
}
