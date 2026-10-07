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

variable "permission_model" {
  description = "SERVICE_MANAGED (AWS Organizations, recomendado) | SELF_MANAGED (cuentas sueltas)."
  type        = string
  default     = "SERVICE_MANAGED"

  validation {
    condition     = contains(["SERVICE_MANAGED", "SELF_MANAGED"], var.permission_model)
    error_message = "permission_model debe ser SERVICE_MANAGED o SELF_MANAGED."
  }
}

variable "call_as" {
  description = "SELF (cuenta de management) | DELEGATED_ADMIN (cuenta registrada como administrador delegado)."
  type        = string
  default     = "SELF"
}

variable "organization_id" {
  description = "ID de la organización (o-xxxxxxxxxx): restringe quién publica en el bus central."
  type        = string
}

variable "target_ou_ids" {
  description = "OUs destino (SERVICE_MANAGED), p. ej. [\"ou-abcd-11111111\"]."
  type        = list(string)
  default     = []
}

variable "target_account_ids" {
  description = "Cuentas destino (SELF_MANAGED)."
  type        = list(string)
  default     = []
}

variable "target_regions" {
  type    = list(string)
  default = ["us-east-1", "us-west-2"]
}

variable "audit_account_id" {
  description = "Cuenta de seguridad que asume el rol de auditoría (null = esta cuenta)."
  type        = string
  default     = null
}

variable "enable_config_rules" {
  type    = bool
  default = false
}

variable "baseline_version" {
  type    = string
  default = "1.0.0"
}

variable "max_concurrent_percentage" {
  type    = number
  default = 25
}

variable "failure_tolerance_percentage" {
  type    = number
  default = 10
}

variable "security_emails" {
  type    = list(string)
  default = []
}
