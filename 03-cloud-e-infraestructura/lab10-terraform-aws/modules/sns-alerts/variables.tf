variable "name" {
  type = string
}

variable "kms_key_arn" {
  description = "CMK (su política debe permitir cloudwatch.amazonaws.com y events.amazonaws.com). null = sin cifrado con CMK."
  type        = string
  default     = null
}

variable "email_subscriptions" {
  description = "Correos que recibirán alertas (cada uno debe confirmar la suscripción)."
  type        = list(string)
  default     = []
}

variable "tags" {
  type    = map(string)
  default = {}
}
