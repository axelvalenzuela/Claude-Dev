variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "lab10"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "owner" {
  type = string
}

variable "cost_center" {
  type    = string
  default = "training"
}

variable "model_id" {
  type    = string
  default = "amazon.nova-lite-v1:0"
}

variable "language_code" {
  description = "Idioma para Comprehend (es, en, ...)."
  type        = string
  default     = "es"
}

variable "document_retention_days" {
  description = "Los documentos fuente se eliminan tras N días (minimización de datos)."
  type        = number
  default     = 30
}

variable "alert_emails" {
  type    = list(string)
  default = []
}
