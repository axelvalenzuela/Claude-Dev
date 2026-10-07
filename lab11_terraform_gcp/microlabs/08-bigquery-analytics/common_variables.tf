# Variables comunes a todos los micro labs de GCP (archivo idéntico en cada lab).

variable "project_id" {
  type = string
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

variable "build_service_account" {
  description = "Output build_service_account del lab 00 (projects/<p>/serviceAccounts/<email>). null = SA predeterminada de Cloud Build."
  type        = string
  default     = null
}
