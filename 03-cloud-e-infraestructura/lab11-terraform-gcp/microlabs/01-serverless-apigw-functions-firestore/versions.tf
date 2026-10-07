terraform {
  required_version = ">= 1.10.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.12"
    }
  }

  # Configuración parcial: bucket/prefix se pasan con -backend-config (ver README y CI).
  backend "gcs" {}
}

provider "google" {
  project        = var.project_id
  region         = var.region
  default_labels = local.common_labels
}

provider "google-beta" {
  project        = var.project_id
  region         = var.region
  default_labels = local.common_labels
}
