terraform {
  required_version = ">= 1.10.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.12"
    }
  }

  # El bootstrap se aplica primero con estado LOCAL (el bucket aún no existe).
  # Después: descomenta y ejecuta  terraform init -migrate-state -backend-config=bucket=<tf_state_bucket>
  # backend "gcs" {}
}

provider "google" {
  project        = var.project_id
  region         = var.region
  default_labels = local.common_labels
}
