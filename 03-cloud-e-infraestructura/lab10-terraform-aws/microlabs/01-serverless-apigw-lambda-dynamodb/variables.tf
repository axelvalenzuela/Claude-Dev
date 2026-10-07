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

variable "stage_name" {
  type    = string
  default = "v1"
}

variable "throttle_rate_limit" {
  description = "Solicitudes por segundo en estado estable (usage plan)."
  type        = number
  default     = 50
}

variable "throttle_burst_limit" {
  type    = number
  default = 100
}

variable "monthly_quota" {
  description = "Cuota mensual de solicitudes por API key."
  type        = number
  default     = 100000
}

variable "waf_rate_limit_per_5min" {
  description = "Máximo de solicitudes por IP cada 5 minutos antes de bloquear."
  type        = number
  default     = 1000
}

variable "enable_waf" {
  type    = bool
  default = true
}

variable "enable_fault_injection" {
  description = "Permite provocar errores 5XX con el header x-fault-injection (prácticas de SLO del lab 07). Nunca en prod."
  type        = bool
  default     = false
}

variable "log_retention_days" {
  type    = number
  default = 30
}
