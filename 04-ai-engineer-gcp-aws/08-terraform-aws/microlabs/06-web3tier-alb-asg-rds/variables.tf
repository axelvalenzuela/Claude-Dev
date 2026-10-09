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
  type    = string
  default = "10.60.0.0/16"
}

variable "az_count" {
  type    = number
  default = 2
}

variable "single_nat_gateway" {
  type    = bool
  default = true
}

variable "certificate_arn" {
  type    = string
  default = null
}

variable "app_instance_type" {
  type    = string
  default = "t4g.micro"
}

variable "app_min_size" {
  type    = number
  default = 2
}

variable "app_max_size" {
  type    = number
  default = 4
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_allocated_storage_gb" {
  type    = number
  default = 20
}

variable "db_multi_az" {
  type    = bool
  default = true
}

variable "deletion_protection" {
  type    = bool
  default = false
}
