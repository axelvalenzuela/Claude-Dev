variable "api_state_bucket" {
  description = "Bucket de estado (TF_STATE_BUCKET). Si se define, el servicio y el host se leen del micro lab 01."
  type        = string
  default     = null
}

variable "run_service_name" {
  description = "Servicio de Cloud Run a observar (ignorado si api_state_bucket está definido)."
  type        = string
  default     = "aie-dev-api-items"
}

variable "uptime_host" {
  description = "Host público para el uptime check (gateway del micro lab 01, sin https://)."
  type        = string
  default     = "example.com"
}

variable "availability_goal" {
  type    = number
  default = 0.995

  validation {
    condition     = var.availability_goal > 0.9 && var.availability_goal < 1
    error_message = "availability_goal debe estar entre 0.9 y 1."
  }
}

variable "latency_goal" {
  type    = number
  default = 0.95
}

variable "latency_threshold_ms" {
  type    = number
  default = 800
}

variable "alert_emails" {
  type    = list(string)
  default = []
}

variable "runbook_url" {
  type    = string
  default = "https://github.com/<usuario>/ai-engineer-gcp-aws/wiki/runbook-api-aie"
}
