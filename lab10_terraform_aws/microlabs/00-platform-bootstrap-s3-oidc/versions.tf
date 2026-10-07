terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # El bootstrap se aplica primero con estado LOCAL (huevo-gallina: el bucket aún no existe).
  # Después de crearlo, descomenta y ejecuta: terraform init -migrate-state
  # backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}
