variable "name" {
  type = string
}

variable "project_id" {
  description = "Globalmente único, 6-30 caracteres."
  type        = string
}

variable "folder_id" {
  type = string
}

variable "billing_account" {
  type = string
}

variable "services" {
  type    = list(string)
  default = []
}

variable "operator_members" {
  type    = list(string)
  default = []
}

variable "monthly_budget" {
  type    = number
  default = 20
}

variable "deletion_policy" {
  description = "PREVENT en producción; DELETE permite terraform destroy en el lab."
  type        = string
  default     = "DELETE"
}

variable "labels" {
  type    = map(string)
  default = {}
}
