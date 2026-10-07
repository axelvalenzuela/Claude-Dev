variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "lab10"
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
  default = "10.80.0.0/16"
}

variable "engine_version" {
  description = "null = versión por defecto. Lista: aws neptune describe-db-engine-versions --engine neptune"
  type        = string
  default     = null
}

variable "neptune_family" {
  description = "Familia del parameter group; debe coincidir con la versión del motor (neptune1.3, neptune1.4, ...)."
  type        = string
  default     = "neptune1.4"
}

variable "min_ncu" {
  description = "Mínimo de Neptune Capacity Units (1 NCU ≈ 2 GiB RAM)."
  type        = number
  default     = 1
}

variable "max_ncu" {
  type    = number
  default = 4
}

variable "instance_count" {
  description = "1 = writer; 2+ = writer + réplicas de lectura en otras AZ (alta disponibilidad)."
  type        = number
  default     = 1
}

variable "backup_retention_days" {
  type    = number
  default = 7
}

variable "deletion_protection" {
  type    = bool
  default = false
}
