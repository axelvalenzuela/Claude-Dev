variable "name" {
  type = string
}

variable "hash_key" {
  type = string
}

variable "hash_key_type" {
  description = "S | N | B"
  type        = string
  default     = "S"
}

variable "range_key" {
  type    = string
  default = null
}

variable "range_key_type" {
  type    = string
  default = "S"
}

variable "global_secondary_indexes" {
  type = list(object({
    name            = string
    hash_key        = string
    hash_key_type   = optional(string, "S")
    range_key       = optional(string)
    range_key_type  = optional(string, "S")
    projection_type = optional(string, "ALL")
  }))
  default = []
}

variable "ttl_attribute" {
  description = "Atributo epoch (segundos) para expirar ítems automáticamente (null = sin TTL)."
  type        = string
  default     = null
}

variable "stream_enabled" {
  type    = bool
  default = false
}

variable "point_in_time_recovery" {
  type    = bool
  default = true
}

variable "deletion_protection" {
  description = "Recomendado true en producción."
  type        = bool
  default     = false
}

variable "kms_key_arn" {
  description = "null = llave propiedad de AWS."
  type        = string
  default     = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
