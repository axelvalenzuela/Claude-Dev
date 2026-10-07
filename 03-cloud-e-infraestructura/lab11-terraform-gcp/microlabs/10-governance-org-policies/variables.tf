variable "org_id" {
  description = "ID numérico de la organización (gcloud organizations list)."
  type        = string
}

variable "parent_folder_id" {
  description = "Carpeta sandbox donde crear la jerarquía del lab (recomendado). null = raíz de la organización."
  type        = string
  default     = null
}

variable "billing_account" {
  type = string
}

variable "environments" {
  type    = list(string)
  default = ["dev", "prod"]
}

variable "allowed_locations" {
  description = "Value groups o ubicaciones permitidas."
  type        = list(string)
  default     = ["in:us-locations"]
}

variable "prod_denied_services" {
  description = "Servicios prohibidos fuera de dev (gcp.restrictServiceUsage)."
  type        = list(string)
  default     = ["notebooks.googleapis.com", "datafusion.googleapis.com"]
}

variable "baseline_services" {
  type = list(string)
  default = [
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
  ]
}

variable "project_suffix" {
  description = "Sufijo para que los project_id sean globalmente únicos (p. ej. tus iniciales + año)."
  type        = string
}

variable "projects" {
  description = "Proyectos a crear con el baseline."
  type = map(object({
    environment    = string
    operators      = optional(list(string), [])
    extra_services = optional(list(string), [])
    monthly_budget = optional(number, 20)
  }))
  default = {
    "ventas-dev"  = { environment = "dev", extra_services = ["run.googleapis.com"] }
    "ventas-prod" = { environment = "prod", extra_services = ["run.googleapis.com"], monthly_budget = 50 }
  }
}
