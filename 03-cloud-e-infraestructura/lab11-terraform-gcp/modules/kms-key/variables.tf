variable "project_id" {
  type = string
}

variable "name" {
  type = string
}

variable "location" {
  description = "Debe coincidir con la ubicación de los recursos que cifra (región o multirregión)."
  type        = string
}

variable "rotation_period" {
  description = "Rotación automática (90 días)."
  type        = string
  default     = "7776000s"
}

variable "encrypter_members" {
  description = "Members con encrypt/decrypt, p. ej. serviceAccount:service-<num>@gs-project-accounts.iam.gserviceaccount.com."
  type        = list(string)
  default     = []
}
