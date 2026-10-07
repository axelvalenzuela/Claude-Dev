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
  description = "Correo o usuario responsable (etiqueta Owner)."
  type        = string
}

variable "cost_center" {
  type    = string
  default = "training"
}

variable "gitlab_host" {
  description = "Host de GitLab sin https:// (gitlab.com o tu instancia self-managed)."
  type        = string
  default     = "gitlab.com"
}

variable "gitlab_audience" {
  description = "Audiencia (aud) del id_token de GitLab. Debe coincidir con id_tokens en .gitlab-ci.yml."
  type        = string
  default     = "https://gitlab.com"
}

variable "gitlab_project_path" {
  description = "Ruta del proyecto en GitLab: grupo/subgrupo/proyecto."
  type        = string
}

variable "gitlab_default_branch" {
  type    = string
  default = "main"
}

variable "allowed_regions" {
  description = "Regiones permitidas por el permissions boundary del rol de CI."
  type        = list(string)
  default     = ["us-east-1", "us-west-2"]
}

variable "monthly_budget_usd" {
  description = "Presupuesto mensual para alertas de costo."
  type        = number
  default     = 50
}

variable "alert_emails" {
  type    = list(string)
  default = []
}
