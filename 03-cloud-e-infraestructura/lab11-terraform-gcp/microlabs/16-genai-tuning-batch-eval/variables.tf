variable "data_retention_days" {
  description = "Los datasets y resultados se borran tras N días (minimización de datos)."
  type        = number
  default     = 30
}

variable "notification_channels" {
  type    = list(string)
  default = []
}
