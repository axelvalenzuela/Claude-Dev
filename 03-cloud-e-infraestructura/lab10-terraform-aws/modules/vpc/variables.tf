variable "name" {
  type = string
}

variable "region" {
  description = "Región (para nombres de servicio de los VPC endpoints)."
  type        = string
}

variable "cidr_block" {
  type    = string
  default = "10.10.0.0/16"
}

variable "az_count" {
  description = "Número de AZs (mínimo 2 para alta disponibilidad)."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "az_count debe estar entre 2 y 3."
  }
}

variable "enable_nat_gateway" {
  description = "Salida a Internet para la capa app (costo ~USD 32/mes por NAT + datos)."
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "true = un NAT compartido (barato, punto único de falla). false = uno por AZ."
  type        = bool
  default     = true
}

variable "enable_gateway_endpoints" {
  type    = bool
  default = true
}

variable "interface_endpoints" {
  description = "Servicios para interface endpoints, p. ej. [\"secretsmanager\", \"ssm\"]."
  type        = list(string)
  default     = []
}

variable "enable_flow_logs" {
  type    = bool
  default = true
}

variable "flow_logs_retention_days" {
  type    = number
  default = 14
}

variable "kms_key_arn" {
  type    = string
  default = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
