variable "quota_per_minute" {
  description = "Requests por minuto por API key (cuota de API Gateway)."
  type        = number
  default     = 120
}

variable "enable_fault_injection" {
  description = "Permite provocar 500 con el header x-fault-injection (prácticas del micro lab 07). Nunca en prod."
  type        = bool
  default     = false
}

variable "max_instances" {
  type    = number
  default = 5
}
