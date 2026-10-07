variable "source_subnet_cidr" {
  type    = string
  default = "10.90.0.0/24"
}

variable "create_demo_source" {
  description = "Crea una VM con PostgreSQL 15 + pglogical y datos de ejemplo (simula on-prem)."
  type        = bool
  default     = true
}

variable "source_host" {
  description = "IP de tu PostgreSQL real (si create_demo_source = false). Debe ser alcanzable por VPN/Interconnect."
  type        = string
  default     = null
}

variable "destination_tier" {
  type    = string
  default = "db-custom-1-3840"
}
