variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "name" {
  type = string
}

variable "description" {
  type    = string
  default = ""
}

variable "source_dir" {
  description = "Directorio con main.py y requirements.txt."
  type        = string
}

variable "source_bucket" {
  description = "Bucket donde se sube el zip del código."
  type        = string
}

variable "runtime" {
  type    = string
  default = "python313"
}

variable "entry_point" {
  type    = string
  default = "handler"
}

variable "build_service_account" {
  description = "SA de Cloud Build (projects/<p>/serviceAccounts/<email>). null = la predeterminada del proyecto."
  type        = string
  default     = null
}

variable "service_account_email" {
  description = "Identidad en tiempo de ejecución (dedicada, mínimo privilegio)."
  type        = string
}

variable "memory" {
  type    = string
  default = "256Mi"
}

variable "cpu" {
  type    = string
  default = "0.1666"
}

variable "timeout_seconds" {
  type    = number
  default = 30
}

variable "min_instances" {
  type    = number
  default = 0
}

variable "max_instances" {
  description = "Tope de escalado: protege dependencias y el presupuesto."
  type        = number
  default     = 5
}

variable "concurrency" {
  description = "Requests simultáneos por instancia (>1 requiere cpu >= 1)."
  type        = number
  default     = 1
}

variable "ingress_settings" {
  description = "ALLOW_ALL | ALLOW_INTERNAL_ONLY | ALLOW_INTERNAL_AND_GCLB"
  type        = string
  default     = "ALLOW_ALL"
}

variable "environment" {
  type    = map(string)
  default = {}
}

variable "vpc_connector" {
  type    = string
  default = null
}

variable "event_trigger" {
  description = "Trigger de Eventarc (null = función HTTP)."
  type = object({
    event_type            = string
    pubsub_topic          = optional(string)
    retry                 = optional(bool, true)
    service_account_email = optional(string)
    filters               = optional(map(string), {})
  })
  default = null
}

variable "invoker_members" {
  description = "Quién puede invocar (p. ej. serviceAccount:..., user:...). Vacío = nadie sin permisos explícitos."
  type        = list(string)
  default     = []
}

variable "labels" {
  type    = map(string)
  default = {}
}
