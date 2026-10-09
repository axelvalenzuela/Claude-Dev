# Módulo: bucket de Cloud Storage seguro por defecto.
# - Uniform bucket-level access (sin ACLs) y Public Access Prevention = enforced
# - Versionado, CMEK opcional, soft delete, lifecycle de costos, retention lock opcional

resource "google_storage_bucket" "this" {
  name                        = var.name
  project                     = var.project_id
  location                    = var.location
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.force_destroy
  labels                      = var.labels

  versioning {
    enabled = var.versioning
  }

  soft_delete_policy {
    retention_duration_seconds = var.soft_delete_days * 86400
  }

  dynamic "encryption" {
    for_each = var.kms_key_name == null ? [] : [var.kms_key_name]
    content {
      default_kms_key_name = encryption.value
    }
  }

  # Versiones antiguas: se eliminan tras N días
  lifecycle_rule {
    condition {
      days_since_noncurrent_time = var.noncurrent_version_days
      with_state                 = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  dynamic "lifecycle_rule" {
    for_each = var.nearline_after_days == null ? [] : [var.nearline_after_days]
    content {
      condition {
        age = lifecycle_rule.value
      }
      action {
        type          = "SetStorageClass"
        storage_class = "NEARLINE"
      }
    }
  }

  dynamic "lifecycle_rule" {
    for_each = var.expiration_days == null ? [] : [var.expiration_days]
    content {
      condition {
        age = lifecycle_rule.value
      }
      action {
        type = "Delete"
      }
    }
  }

  dynamic "retention_policy" {
    for_each = var.retention_days == null ? [] : [var.retention_days]
    content {
      retention_period = retention_policy.value * 86400
      is_locked        = var.lock_retention
    }
  }

  dynamic "logging" {
    for_each = var.access_log_bucket == null ? [] : [var.access_log_bucket]
    content {
      log_bucket        = logging.value
      log_object_prefix = var.name
    }
  }
}
