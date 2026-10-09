variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "aie"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "owner" {
  type = string
}

variable "cost_center" {
  type    = string
  default = "training"
}

variable "vpc_cidr" {
  description = "No debe traslaparse con la red on-premises."
  type        = string
  default     = "10.90.0.0/16"
}

variable "enable_nat_gateway" {
  description = "Salida a Internet de los servidores migrados (parches, licencias)."
  type        = bool
  default     = false
}

variable "source_cidrs" {
  description = "Rangos públicos/privados de los servidores origen que replican por TCP 1500."
  type        = list(string)
}

variable "replication_over_private_link" {
  description = "true = replicación por VPN/Direct Connect (PRIVATE_IP). false = por Internet con IP pública (cifrada TLS)."
  type        = bool
  default     = false
}

variable "bandwidth_throttle_mbps" {
  description = "Límite de ancho de banda de replicación por servidor (0 = sin límite)."
  type        = number
  default     = 0
}

variable "replication_server_instance_type" {
  type    = string
  default = "t3.small"
}

variable "target_app_ports" {
  description = "Puertos que la aplicación migrada expone dentro de la VPC."
  type        = list(number)
  default     = [80, 443]
}

variable "installer_principal_arns" {
  description = "Principals IAM (usuarios SSO/roles) que pueden asumir el rol instalador del agente."
  type        = list(string)
  default     = []
}
