variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "data_subnet_ids" {
  type = list(string)
}

variable "engine_major_version" {
  type    = string
  default = "17"
}

variable "instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_name" {
  type    = string
  default = "appdb"
}

variable "allocated_storage_gb" {
  description = "Mínimo para gp3 en PostgreSQL: 20 GB."
  type        = number
  default     = 20
}

variable "max_allocated_storage_gb" {
  description = "Storage autoscaling hasta este tope."
  type        = number
  default     = 100
}

variable "multi_az" {
  description = "Standby síncrono en otra AZ (duplica el costo; obligatorio en producción)."
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  type    = number
  default = 7
}

variable "deletion_protection" {
  type    = bool
  default = false
}

variable "kms_key_arn" {
  type    = string
  default = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
