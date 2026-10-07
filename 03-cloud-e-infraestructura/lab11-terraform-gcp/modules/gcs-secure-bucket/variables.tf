variable "project_id" {
  type = string
}

variable "name" {
  description = "Nombre global único del bucket."
  type        = string
}

variable "location" {
  description = "Región (us-central1) o multirregión (US)."
  type        = string
}

variable "kms_key_name" {
  description = "CMEK (projects/.../cryptoKeys/...). null = llave administrada por Google."
  type        = string
  default     = null
}

variable "versioning" {
  type    = bool
  default = true
}

variable "force_destroy" {
  description = "Permite borrar el bucket con objetos (solo labs)."
  type        = bool
  default     = true
}

variable "soft_delete_days" {
  description = "Días de recuperación tras borrar objetos (0 = deshabilitado, 7 = mínimo si se usa)."
  type        = number
  default     = 7
}

variable "noncurrent_version_days" {
  type    = number
  default = 30
}

variable "nearline_after_days" {
  type    = number
  default = null
}

variable "expiration_days" {
  type    = number
  default = null
}

variable "retention_days" {
  description = "Retención mínima de objetos (WORM). null = sin retención."
  type        = number
  default     = null
}

variable "lock_retention" {
  description = "Bloquea la retención de forma IRREVERSIBLE (solo cumplimiento real)."
  type        = bool
  default     = false
}

variable "access_log_bucket" {
  type    = string
  default = null
}

variable "labels" {
  type    = map(string)
  default = {}
}
