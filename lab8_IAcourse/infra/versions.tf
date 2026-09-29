terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0, < 8.0"
    }
  }

  # Estado remoto (recomendado en equipo): descomenta y crea antes el bucket.
  # Con estado local, el archivo terraform.tfstate queda en esta carpeta y NO se sube a git.
  # backend "gcs" {
  #   bucket = "TU-PROYECTO-tfstate"
  #   prefix = "lab8"
  # }
}

provider "google" {
  project = var.proyecto
  region  = var.region

  # Necesario para el presupuesto (billingbudgets) cuando usas tus credenciales de usuario (ADC).
  user_project_override = true
  billing_project       = var.proyecto
}
