# Módulo: Cloud Run functions (Cloud Functions gen2) desplegada DESDE CÓDIGO FUENTE.
# Terraform empaqueta el directorio, lo sube a GCS y Cloud Build construye el contenedor:
# no hace falta Docker ni un pipeline de imágenes aparte.

data "archive_file" "src" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.root}/.build/${var.name}.zip"
}

resource "google_storage_bucket_object" "src" {
  # El hash en el nombre fuerza un nuevo build solo cuando cambia el código.
  name   = "functions/${var.name}-${data.archive_file.src.output_md5}.zip"
  bucket = var.source_bucket
  source = data.archive_file.src.output_path
}

resource "google_cloudfunctions2_function" "this" {
  name        = var.name
  project     = var.project_id
  location    = var.region
  description = var.description
  labels      = var.labels

  build_config {
    runtime         = var.runtime
    entry_point     = var.entry_point
    service_account = var.build_service_account
    source {
      storage_source {
        bucket = var.source_bucket
        object = google_storage_bucket_object.src.name
      }
    }
  }

  service_config {
    available_memory                 = var.memory
    available_cpu                    = var.cpu
    timeout_seconds                  = var.timeout_seconds
    min_instance_count               = var.min_instances
    max_instance_count               = var.max_instances
    max_instance_request_concurrency = var.concurrency
    service_account_email            = var.service_account_email
    ingress_settings                 = var.ingress_settings
    all_traffic_on_latest_revision   = true
    environment_variables            = var.environment
    vpc_connector                    = var.vpc_connector
    vpc_connector_egress_settings    = var.vpc_connector == null ? null : "PRIVATE_RANGES_ONLY"
  }

  dynamic "event_trigger" {
    for_each = var.event_trigger == null ? [] : [var.event_trigger]
    content {
      trigger_region        = var.region
      event_type            = event_trigger.value.event_type
      pubsub_topic          = event_trigger.value.pubsub_topic
      retry_policy          = event_trigger.value.retry ? "RETRY_POLICY_RETRY" : "RETRY_POLICY_DO_NOT_RETRY"
      service_account_email = event_trigger.value.service_account_email

      dynamic "event_filters" {
        for_each = event_trigger.value.filters
        content {
          attribute = event_filters.key
          value     = event_filters.value
        }
      }
    }
  }
}

# Gen2 corre sobre Cloud Run: el permiso de invocación es run.invoker sobre el servicio.
resource "google_cloud_run_service_iam_member" "invoker" {
  for_each = toset(var.invoker_members)
  project  = var.project_id
  location = var.region
  service  = google_cloudfunctions2_function.this.name
  role     = "roles/run.invoker"
  member   = each.value
}
