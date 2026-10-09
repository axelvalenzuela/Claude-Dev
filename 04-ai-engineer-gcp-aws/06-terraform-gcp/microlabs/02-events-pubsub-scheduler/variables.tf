variable "max_delivery_attempts" {
  description = "Entregas antes de mover el mensaje al dead letter topic (5-100)."
  type        = number
  default     = 5
}

variable "audit_retention_days" {
  type    = number
  default = 30
}

variable "report_schedule" {
  description = "Cron de Cloud Scheduler."
  type        = string
  default     = "0 * * * *"
}

variable "schedule_timezone" {
  type    = string
  default = "America/Tijuana"
}

variable "notification_channels" {
  description = "IDs de canales de Cloud Monitoring (p. ej. el email del micro lab 00)."
  type        = list(string)
  default     = []
}
