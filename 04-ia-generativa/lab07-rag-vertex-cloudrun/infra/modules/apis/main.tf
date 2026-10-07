variable "project_id" {
  type = string
}

variable "services" {
  type        = list(string)
  description = "APIs to enable. Defaults cover everything this lab needs: Vertex AI calls, Cloud Run itself, and building/storing the container image."
  default = [
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
  ]
}

resource "google_project_service" "this" {
  for_each = toset(var.services)

  project = var.project_id
  service = each.value

  # false on purpose: destroying this module must not disable an API that
  # some other service in the same project also depends on.
  disable_on_destroy = false
}

output "enabled_services" {
  value = [for s in google_project_service.this : s.service]
}
