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

variable "field_log_level" {
  description = "NONE | ERROR | ALL (ALL solo para depurar: costoso y puede registrar datos)."
  type        = string
  default     = "ERROR"
}

variable "query_depth_limit" {
  description = "Profundidad máxima de consultas (protege contra consultas abusivas)."
  type        = number
  default     = 5
}

variable "enable_cache" {
  type    = bool
  default = false
}

variable "log_retention_days" {
  type    = number
  default = 30
}
