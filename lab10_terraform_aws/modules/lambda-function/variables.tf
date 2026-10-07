variable "function_name" {
  type = string
}

variable "description" {
  type    = string
  default = ""
}

variable "source_dir" {
  description = "Directorio con el código fuente a empaquetar."
  type        = string
}

variable "handler" {
  type    = string
  default = "app.handler"
}

variable "runtime" {
  type    = string
  default = "python3.13"
}

variable "architectures" {
  type    = list(string)
  default = ["arm64"]
}

variable "memory_size" {
  type    = number
  default = 256
}

variable "timeout" {
  type    = number
  default = 10
}

variable "environment" {
  type    = map(string)
  default = {}
}

variable "attach_inline_policy" {
  description = "true si se pasa inline_policy_json (bandera estática para count)."
  type        = bool
  default     = false
}

variable "inline_policy_json" {
  type    = string
  default = null
}

variable "managed_policy_arns" {
  description = "Mapa nombre => ARN de políticas administradas adicionales."
  type        = map(string)
  default     = {}
}

variable "permissions_boundary_arn" {
  type    = string
  default = null
}

variable "log_retention_days" {
  type    = number
  default = 30
}

variable "kms_key_arn" {
  description = "CMK para cifrar variables de entorno y logs (opcional)."
  type        = string
  default     = null
}

variable "tracing_mode" {
  description = "Active | PassThrough"
  type        = string
  default     = "Active"
}

variable "reserved_concurrency" {
  description = "-1 = sin reserva. Úsalo para limitar el radio de impacto y proteger dependencias."
  type        = number
  default     = -1
}

variable "vpc_subnet_ids" {
  type    = list(string)
  default = []
}

variable "vpc_security_group_ids" {
  type    = list(string)
  default = []
}

variable "dead_letter_target_arn" {
  description = "ARN de SQS/SNS para invocaciones asíncronas fallidas (el rol debe poder enviar)."
  type        = string
  default     = null
}

variable "layers" {
  type    = list(string)
  default = []
}

variable "tags" {
  type    = map(string)
  default = {}
}
