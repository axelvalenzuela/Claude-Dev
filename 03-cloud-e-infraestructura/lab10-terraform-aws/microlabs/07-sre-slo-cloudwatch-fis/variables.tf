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

variable "api_name" {
  description = "Nombre del API REST a observar (output del micro lab 01: lab10-dev-api)."
  type        = string
  default     = "lab10-dev-api"
}

variable "api_stage" {
  type    = string
  default = "v1"
}

variable "api_access_log_group" {
  type    = string
  default = "/apigw/lab10-dev-api/access"
}

variable "lab01_state_bucket" {
  description = "Bucket de estado (TF_STATE_BUCKET). Si se define, api_* y health_check_url se leen del lab 01."
  type        = string
  default     = null
}

variable "health_check_url" {
  description = "URL pública que vigila el canary (p. ej. <api_url>/health). Ignorada si lab01_state_bucket está definido."
  type        = string
  default     = "https://example.com/"
}

variable "slo_target" {
  description = "Objetivo de disponibilidad (0.999 = 99.9 %, ~43 min de presupuesto de error al mes)."
  type        = number
  default     = 0.999

  validation {
    condition     = var.slo_target > 0.9 && var.slo_target < 1
    error_message = "slo_target debe estar entre 0.9 y 1."
  }
}

variable "latency_p99_ms" {
  type    = number
  default = 1000
}

variable "runbook_url" {
  type    = string
  default = "https://gitlab.com/<grupo>/<proyecto>/-/wikis/runbooks/api-availability"
}

variable "alert_emails" {
  type    = list(string)
  default = []
}

variable "canary_runtime_version" {
  description = "Consulta los vigentes con: aws synthetics describe-runtime-versions"
  type        = string
  default     = "syn-nodejs-puppeteer-9.1"
}

variable "slack_team_id" {
  description = "ID del workspace de Slack (vacío = sin ChatOps)."
  type        = string
  default     = ""
}

variable "slack_channel_id" {
  type    = string
  default = ""
}

variable "enable_fis" {
  type    = bool
  default = false
}

variable "fis_target_tag_key" {
  type    = string
  default = "MicroLab"
}

variable "fis_target_tag_value" {
  type    = string
  default = "06-web3tier-alb-asg-rds"
}
