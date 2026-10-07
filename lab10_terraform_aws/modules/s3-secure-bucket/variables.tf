variable "bucket_name" {
  description = "Nombre global único del bucket."
  type        = string
}

variable "kms_key_arn" {
  description = "ARN de la CMK. Si es null se usa SSE-S3 (AES256)."
  type        = string
  default     = null
}

variable "versioning" {
  type    = bool
  default = true
}

variable "force_destroy" {
  description = "Permite destruir el bucket con objetos (solo labs; false en producción)."
  type        = bool
  default     = true
}

variable "noncurrent_version_expiration_days" {
  type    = number
  default = 30
}

variable "expiration_days" {
  description = "Expira objetos actuales tras N días (null = nunca)."
  type        = number
  default     = null
}

variable "transition_to_ia_days" {
  description = "Mueve objetos a STANDARD_IA tras N días (null = no). Mínimo 30."
  type        = number
  default     = null
}

variable "access_log_bucket" {
  description = "Bucket destino de server access logs (null = deshabilitado)."
  type        = string
  default     = null
}

variable "additional_policy_json" {
  description = "Política JSON adicional que se fusiona con la política base."
  type        = string
  default     = null
}

variable "enable_eventbridge_notifications" {
  description = "Envía eventos del bucket a EventBridge (default bus)."
  type        = bool
  default     = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
