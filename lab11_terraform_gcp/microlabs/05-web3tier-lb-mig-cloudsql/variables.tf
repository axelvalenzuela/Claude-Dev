variable "app_subnet_cidr" {
  type    = string
  default = "10.50.0.0/24"
}

variable "app_port" {
  type    = number
  default = 8080
}

variable "machine_type" {
  type    = string
  default = "e2-small"
}

variable "min_replicas" {
  type    = number
  default = 2
}

variable "max_replicas" {
  type    = number
  default = 4
}

variable "db_version" {
  type    = string
  default = "POSTGRES_16"
}

variable "db_tier" {
  description = "db-custom-<vCPU>-<MB>. Los tiers shared-core (db-f1-micro) no tienen SLA."
  type        = string
  default     = "db-custom-1-3840"
}

variable "db_high_availability" {
  description = "REGIONAL = standby síncrono en otra zona (duplica el costo)."
  type        = bool
  default     = true
}

variable "db_disk_gb" {
  description = "Mínimo 10 GB; autoresize habilitado."
  type        = number
  default     = 10
}

variable "rate_limit_per_minute" {
  type    = number
  default = 300
}

variable "domain" {
  description = "Dominio para HTTPS administrado (null = solo HTTP, aceptable solo en laboratorio)."
  type        = string
  default     = null
}

variable "deletion_protection" {
  type    = bool
  default = false
}
