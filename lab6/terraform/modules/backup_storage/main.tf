variable "bucket_name" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

variable "transition_to_glacier_days" {
  type    = number
  default = 30
}

variable "retention_days" {
  type    = number
  default = 365
}

variable "force_destroy" {
  type        = bool
  default     = false
  description = "Permite borrar el bucket con objetos (solo laboratorio)."
}

variable "tags" {
  type    = map(string)
  default = {}
}

module "bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 4.0"

  bucket        = var.bucket_name
  force_destroy = var.force_destroy

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  control_object_ownership = true
  object_ownership         = "BucketOwnerEnforced"

  attach_deny_insecure_transport_policy = true

  versioning = {
    enabled = true
  }

  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm     = "aws:kms"
        kms_master_key_id = var.kms_key_arn
      }
      bucket_key_enabled = true
    }
  }

  lifecycle_rule = [
    {
      id      = "archive-and-expire"
      enabled = true
      filter  = {}

      transition = [
        {
          days          = var.transition_to_glacier_days
          storage_class = "GLACIER"
        }
      ]

      expiration = {
        days = var.retention_days
      }

      noncurrent_version_expiration = {
        days = 30
      }
    }
  ]

  tags = var.tags
}

output "bucket_name" {
  value = module.bucket.s3_bucket_id
}

output "bucket_arn" {
  value = module.bucket.s3_bucket_arn
}
