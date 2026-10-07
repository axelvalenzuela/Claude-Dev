variable "bq_location" {
  description = "Ubicación de BigQuery (US multirregión o una región)."
  type        = string
  default     = "US"
}

variable "raw_retention_days" {
  description = "Expiración de particiones crudas (minimización de datos y costo)."
  type        = number
  default     = 90
}

variable "kpi_schedule" {
  description = "Formato de Data Transfer Service."
  type        = string
  default     = "every day 06:00"
}

variable "analyst_members" {
  description = "Analistas con acceso SOLO a las vistas compartidas, p. ej. [\"group:analistas@dominio.com\"]."
  type        = list(string)
  default     = []
}
