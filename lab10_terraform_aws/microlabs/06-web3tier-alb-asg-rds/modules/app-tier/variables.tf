variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "app_subnet_ids" {
  type = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "target_group_arn" {
  type = string
}

variable "app_port" {
  type    = number
  default = 80
}

variable "instance_type" {
  description = "Graviton (t4g) por precio/rendimiento."
  type        = string
  default     = "t4g.micro"
}

variable "root_volume_gb" {
  type    = number
  default = 8
}

variable "min_size" {
  type    = number
  default = 2
}

variable "max_size" {
  type    = number
  default = 4
}

variable "cpu_target" {
  type    = number
  default = 50
}

variable "region" {
  type = string
}

variable "db_endpoint" {
  type = string
}

variable "db_name" {
  type    = string
  default = "appdb"
}

variable "db_secret_arn" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
