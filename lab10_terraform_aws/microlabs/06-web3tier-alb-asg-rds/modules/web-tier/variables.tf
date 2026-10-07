variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "app_port" {
  type    = number
  default = 80
}

variable "health_check_path" {
  type    = string
  default = "/health"
}

variable "certificate_arn" {
  description = "ARN de ACM para HTTPS (null = solo HTTP, aceptable únicamente en laboratorio)."
  type        = string
  default     = null
}

variable "deletion_protection" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
