variable "rai_confidence" {
  description = "Umbral de los filtros RAI: LOW_AND_ABOVE (más estricto), MEDIUM_AND_ABOVE, HIGH."
  type        = string
  default     = "MEDIUM_AND_ABOVE"
}

variable "injection_confidence" {
  description = "Umbral de prompt injection / jailbreak."
  type        = string
  default     = "LOW_AND_ABOVE"
}

variable "model" {
  type    = string
  default = "gemini-2.5-flash"
}

variable "vertex_location" {
  type    = string
  default = "global"
}

variable "invoker_members" {
  description = "Quién puede usar el chat, p. ej. [\"user:tu@correo\"]."
  type        = list(string)
}
