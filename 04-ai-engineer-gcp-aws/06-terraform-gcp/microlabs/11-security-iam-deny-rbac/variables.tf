variable "data_access_audit_services" {
  description = "Servicios con Data Access logs (tienen costo por volumen: elige los sensibles)."
  type        = list(string)
  default     = ["storage.googleapis.com", "secretmanager.googleapis.com", "iam.googleapis.com", "bigquery.googleapis.com"]
}

variable "log_retention_days" {
  type    = number
  default = 365
}

variable "lock_log_bucket" {
  description = "IRREVERSIBLE: impide reducir la retención o borrar el log bucket."
  type        = bool
  default     = false
}

variable "archive_retention_days" {
  type    = number
  default = 365
}

variable "security_emails" {
  type    = list(string)
  default = []
}

variable "protect_audit_sinks" {
  description = "Agrega a la deny policy borrar/editar sinks y log buckets. Requiere tu identidad en deny_exception_principals para poder destruir el lab."
  type        = bool
  default     = false
}

variable "deny_exception_principals" {
  description = "Excepciones a la deny policy, formato principal://goog/subject/<email> o principalSet://goog/group/<email>."
  type        = list(string)
  default     = []
}

variable "rbac_members" {
  description = "Miembros por función: developer, sre, auditor, finops."
  type        = map(list(string))
  default     = {}
}

variable "break_glass_members" {
  type    = list(string)
  default = []
}

variable "break_glass_until" {
  description = "Fecha RFC 3339 hasta la que vale el acceso de emergencia (null = desactivado)."
  type        = string
  default     = null
}

variable "org_id" {
  description = "Para notificaciones de Security Command Center (null = omitir)."
  type        = string
  default     = null
}

variable "access_policy_id" {
  description = "Access Context Manager policy para VPC Service Controls (null = omitir)."
  type        = string
  default     = null
}
