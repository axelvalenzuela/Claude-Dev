variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "service_name" {
  type = string
}

variable "container_image" {
  type        = string
  description = "Full Artifact Registry image URI. Built and pushed separately (see ../../README.md) — this module only points Cloud Run at it."
}

variable "service_account_email" {
  type        = string
  description = "Runtime identity for the container. Pass a dedicated, least-privilege SA (see modules/service_account) instead of the default compute SA."
}

variable "env_vars" {
  type        = map(string)
  description = "Environment variables the container reads at startup (src/config.py)."
  default     = {}
}

variable "allow_unauthenticated" {
  type        = bool
  description = "true = anyone with the URL can use the chat page. false = only callers with a valid identity token can invoke it."
  default     = true
}

variable "min_instance_count" {
  type        = number
  description = "0 = scale to zero, $0 while nobody is using the demo. >0 avoids cold starts but keeps at least one instance billed."
  default     = 0
}

variable "max_instance_count" {
  type    = number
  default = 2
}

variable "cpu" {
  type        = string
  description = "This app is I/O-bound (waiting on Vertex AI HTTP calls), not CPU-bound — 1 vCPU is generous for a lab-sized index."
  default     = "1"
}

variable "memory" {
  type    = string
  default = "512Mi"
}

resource "google_cloud_run_v2_service" "this" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  launch_stage = "GA"

  template {
    service_account = var.service_account_email

    containers {
      image = var.container_image

      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      startup_probe {
        http_get {
          path = "/api/health"
        }
        initial_delay_seconds = 5
        # The first request into a cold container also builds the RAG
        # index if it's missing (src/main.py's lifespan hook) — give it
        # real time to come up before Cloud Run marks it unhealthy.
        period_seconds     = 5
        failure_threshold  = 6
      }
    }

    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
    }
  }
}

# Optional: only created when the caller wants the service publicly
# reachable without an identity token.
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.this.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "url" {
  value = google_cloud_run_v2_service.this.uri
}

output "service_id" {
  value = google_cloud_run_v2_service.this.id
}
