variable "project_id" {
  type = string
}

variable "account_id" {
  description = "6-30 caracteres: minúsculas, números y guiones."
  type        = string
}

variable "display_name" {
  type    = string
  default = ""
}

variable "description" {
  type    = string
  default = "Administrada por Terraform"
}

variable "project_roles" {
  description = "Roles a nivel de proyecto. Prefiere bindings a nivel de recurso cuando existan."
  type        = list(string)
  default     = []
}
