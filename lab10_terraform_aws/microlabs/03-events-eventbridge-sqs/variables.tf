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

variable "archive_retention_days" {
  description = "Días que se guardan los eventos para replay (0 = indefinido)."
  type        = number
  default     = 7
}

variable "producer_account_ids" {
  description = "Cuentas AWS autorizadas a publicar en el bus (cross-account)."
  type        = list(string)
  default     = []
}

variable "high_value_threshold" {
  type    = number
  default = 1000
}

variable "report_schedule" {
  description = "Expresión rate() o cron() de EventBridge Scheduler."
  type        = string
  default     = "rate(1 hour)"
}

variable "schedule_timezone" {
  type    = string
  default = "America/Tijuana"
}

variable "processor_async_retries" {
  description = "Reintentos de Lambda ante error del código (0-2) antes de enviar a la DLQ."
  type        = number
  default     = 1
}

variable "log_retention_days" {
  type    = number
  default = 14
}
