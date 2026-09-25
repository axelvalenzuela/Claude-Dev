variable "project_id" {
  description = "GCP project id (not name/number) where the lab is deployed."
  type        = string
}

variable "region" {
  description = "Region for Cloud Run and Vertex AI calls. Keep these matched: calling Vertex AI from a different region than the deploy region still works, but adds latency."
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name."
  type        = string
  default     = "lab7-rag-gemini"
}

variable "container_image" {
  description = <<-EOT
    Full Artifact Registry image URI to deploy, e.g.
    us-central1-docker.pkg.dev/PROJECT/lab7/rag-gemini:latest.
    Build and push it first (see infra/README.md) — Terraform here only
    points Cloud Run at an image, it does not build one.
  EOT
  type        = string
}

variable "embedding_model" {
  type    = string
  default = "text-embedding-005"
}

variable "generation_model" {
  type    = string
  default = "gemini-2.5-flash"
}

variable "allow_unauthenticated" {
  description = "true = anyone with the URL can use the chat page (fine for a personal lab demo). false = only callers with an identity token can call it."
  type        = bool
  default     = true
}
