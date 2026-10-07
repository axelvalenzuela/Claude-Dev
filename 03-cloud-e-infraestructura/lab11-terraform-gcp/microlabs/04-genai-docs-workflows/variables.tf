variable "model" {
  type    = string
  default = "gemini-2.5-flash"
}

variable "vertex_location" {
  description = "Región de Vertex AI para el conector de Workflows (no admite 'global')."
  type        = string
  default     = "us-central1"
}

variable "language" {
  description = "Idioma para Natural Language API."
  type        = string
  default     = "es"
}

variable "document_retention_days" {
  type    = number
  default = 30
}

variable "notification_channels" {
  type    = list(string)
  default = []
}
