variable "project_id" {
  type = string
}

variable "services" {
  description = "APIs a habilitar, p. ej. [\"run.googleapis.com\", \"firestore.googleapis.com\"]."
  type        = list(string)
}

variable "propagation_wait" {
  type    = string
  default = "30s"
}
