variable "project_id" {
  type = string
}

variable "name" {
  type = string
}

variable "region" {
  type = string
}

variable "subnets" {
  description = "Mapa nombre => CIDR, p. ej. { app = \"10.10.0.0/24\", data = \"10.10.1.0/24\" }."
  type        = map(string)
}

variable "secondary_ranges" {
  description = "Rangos secundarios por subnet (GKE): { app = { pods = \"10.20.0.0/16\" } }."
  type        = map(map(string))
  default     = {}
}

variable "enable_flow_logs" {
  type    = bool
  default = true
}

variable "enable_nat" {
  type    = bool
  default = true
}

variable "allow_iap_ssh" {
  type    = bool
  default = true
}

variable "health_check_ports" {
  type    = list(string)
  default = []
}

variable "health_check_target_tags" {
  type    = list(string)
  default = []
}

variable "enable_private_service_access" {
  type    = bool
  default = false
}
