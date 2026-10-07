variable "nodes_cidr" {
  type    = string
  default = "10.60.0.0/22"
}

variable "pods_cidr" {
  type    = string
  default = "10.64.0.0/14"
}

variable "services_cidr" {
  type    = string
  default = "10.68.0.0/20"
}

variable "authorized_networks" {
  description = "CIDRs que pueden usar kubectl contra el control plane (tu IP pública /32)."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "image" {
  description = "Imagen non-root que escucha en 8080."
  type        = string
  default     = "nginxinc/nginx-unprivileged:1.27-alpine"
}

variable "min_replicas" {
  type    = number
  default = 2
}

variable "max_replicas" {
  type    = number
  default = 6
}

variable "deletion_protection" {
  type    = bool
  default = false
}
