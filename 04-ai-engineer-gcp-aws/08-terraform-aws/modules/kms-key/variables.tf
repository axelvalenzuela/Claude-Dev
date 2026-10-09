variable "alias" {
  description = "Alias de la llave (sin el prefijo alias/)."
  type        = string
}

variable "description" {
  description = "Descripción de la llave."
  type        = string
  default     = "CMK administrada por Terraform"
}

variable "service_principals" {
  description = "Principals de servicio que pueden usar la llave (p. ej. logs.us-east-1.amazonaws.com, sns.amazonaws.com, cloudwatch.amazonaws.com)."
  type        = list(string)
  default     = []
}

variable "deletion_window_in_days" {
  description = "Días de espera antes de borrar la llave (7-30)."
  type        = number
  default     = 7
}

variable "tags" {
  description = "Etiquetas adicionales."
  type        = map(string)
  default     = {}
}
