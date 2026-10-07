# Micro lab 02 (GCP) - Arquitectura orientada a eventos con Pub/Sub
#   Tópico con schema AVRO (validación al publicar) + retención 7 días (replay con seek)
#   Suscripción PUSH autenticada (OIDC) -> función processor, con reintentos y DEAD LETTER topic
#   Suscripción con FILTRO por atributos (alto valor) · Suscripción BigQuery (auditoría sin código)
#   Cloud Scheduler -> función reporter (HTTP + OIDC)

data "google_project" "this" {}

locals {
  name           = "lab11-${var.environment}-evt"
  pubsub_service = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "02-events-pubsub-scheduler"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services = [
    "pubsub.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudscheduler.googleapis.com",
    "bigquery.googleapis.com",
  ]
}

# ---------------- Contrato del evento ----------------
resource "google_pubsub_schema" "order" {
  name       = "${local.name}-order"
  type       = "AVRO"
  definition = file("${path.module}/schemas/order.avsc")
  depends_on = [module.services]
}

resource "google_pubsub_topic" "orders" {
  name                       = "${local.name}-orders"
  message_retention_duration = "604800s" # 7 días: permite replay con seek

  schema_settings {
    schema   = google_pubsub_schema.order.id
    encoding = "JSON"
  }
}

resource "google_pubsub_topic" "dead_letter" {
  name                       = "${local.name}-dead-letter"
  message_retention_duration = "604800s"
  depends_on                 = [module.services]
}

resource "google_pubsub_subscription" "dead_letter_inspect" {
  name                       = "${local.name}-dead-letter-inspect"
  topic                      = google_pubsub_topic.dead_letter.id
  ack_deadline_seconds       = 30
  message_retention_duration = "1209600s" # 14 días
  expiration_policy {
    ttl = ""
  }
}

# ---------------- Funciones ----------------
module "source_bucket" {
  source          = "../../modules/gcs-secure-bucket"
  project_id      = var.project_id
  name            = "${var.project_id}-${local.name}-src"
  location        = var.region
  expiration_days = 30
  depends_on      = [module.services]
}

module "runtime_sa" {
  source       = "../../modules/service-account"
  project_id   = var.project_id
  account_id   = "${local.name}-fn"
  display_name = "Runtime de funciones del lab 02"
  depends_on   = [module.services]
}

module "invoker_sa" {
  source       = "../../modules/service-account"
  project_id   = var.project_id
  account_id   = "${local.name}-push"
  display_name = "Identidad OIDC de Pub/Sub push y Scheduler"
  depends_on   = [module.services]
}

module "processor" {
  source                = "../../modules/cloud-function"
  project_id            = var.project_id
  region                = var.region
  name                  = "${local.name}-processor"
  description           = "Procesa órdenes (push de Pub/Sub)"
  source_dir            = "${path.module}/src/processor"
  entry_point           = "handler"
  source_bucket         = module.source_bucket.name
  build_service_account = var.build_service_account
  service_account_email = module.runtime_sa.email
  max_instances         = 10
  invoker_members       = [module.invoker_sa.member]
}

module "reporter" {
  source                = "../../modules/cloud-function"
  project_id            = var.project_id
  region                = var.region
  name                  = "${local.name}-reporter"
  description           = "Tarea programada"
  source_dir            = "${path.module}/src/reporter"
  entry_point           = "handler"
  source_bucket         = module.source_bucket.name
  build_service_account = var.build_service_account
  service_account_email = module.runtime_sa.email
  max_instances         = 1
  invoker_members       = [module.invoker_sa.member]
}

# ---------------- Suscripción 1: push autenticado + reintentos + DLQ ----------------
resource "google_pubsub_subscription" "processor" {
  name                       = "${local.name}-processor-push"
  topic                      = google_pubsub_topic.orders.id
  ack_deadline_seconds       = 60
  retain_acked_messages      = true
  message_retention_duration = "604800s"

  push_config {
    push_endpoint = module.processor.uri
    oidc_token {
      service_account_email = module.invoker_sa.email
      audience              = module.processor.uri
    }
    attributes = {
      x-goog-version = "v1"
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "60s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = var.max_delivery_attempts
  }

  expiration_policy {
    ttl = ""
  }
}

# El agente de Pub/Sub reenvía a la DLQ y firma tokens OIDC
resource "google_pubsub_topic_iam_member" "dlq_publisher" {
  topic  = google_pubsub_topic.dead_letter.id
  role   = "roles/pubsub.publisher"
  member = local.pubsub_service
}

resource "google_pubsub_subscription_iam_member" "dlq_subscriber" {
  subscription = google_pubsub_subscription.processor.id
  role         = "roles/pubsub.subscriber"
  member       = local.pubsub_service
}

resource "google_service_account_iam_member" "pubsub_token_creator" {
  service_account_id = module.invoker_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = local.pubsub_service
}

# ---------------- Suscripción 2: filtro por atributos (alto valor) ----------------
resource "google_pubsub_subscription" "high_value" {
  name                       = "${local.name}-high-value"
  topic                      = google_pubsub_topic.orders.id
  filter                     = "attributes.tier = \"high\""
  ack_deadline_seconds       = 30
  message_retention_duration = "604800s"
  enable_message_ordering    = false

  expiration_policy {
    ttl = ""
  }
}

# ---------------- Suscripción 3: auditoría directa a BigQuery ----------------
resource "google_bigquery_dataset" "audit" {
  dataset_id                  = replace("${local.name}_audit", "-", "_")
  location                    = var.region
  default_table_expiration_ms = var.audit_retention_days * 86400000
  delete_contents_on_destroy  = true
  depends_on                  = [module.services]
}

resource "google_bigquery_table" "events" {
  dataset_id          = google_bigquery_dataset.audit.dataset_id
  table_id            = "order_events"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "publish_time"
  }

  schema = jsonencode([
    { name = "subscription_name", type = "STRING", mode = "NULLABLE" },
    { name = "message_id", type = "STRING", mode = "NULLABLE" },
    { name = "publish_time", type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "data", type = "STRING", mode = "NULLABLE" },
    { name = "attributes", type = "STRING", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_dataset_iam_member" "pubsub_writer" {
  dataset_id = google_bigquery_dataset.audit.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = local.pubsub_service
}

resource "google_pubsub_subscription" "audit" {
  name  = "${local.name}-audit-bq"
  topic = google_pubsub_topic.orders.id

  bigquery_config {
    table          = "${var.project_id}.${google_bigquery_table.events.dataset_id}.${google_bigquery_table.events.table_id}"
    write_metadata = true
  }

  expiration_policy {
    ttl = ""
  }

  depends_on = [google_bigquery_dataset_iam_member.pubsub_writer]
}

# ---------------- Cloud Scheduler ----------------
resource "google_cloud_scheduler_job" "report" {
  name             = "${local.name}-hourly-report"
  region           = var.region
  schedule         = var.report_schedule
  time_zone        = var.schedule_timezone
  attempt_deadline = "60s"

  retry_config {
    retry_count = 2
  }

  http_target {
    uri         = module.reporter.uri
    http_method = "POST"
    body        = base64encode(jsonencode({ report = "orders-summary" }))
    headers = {
      "Content-Type" = "application/json"
    }
    oidc_token {
      service_account_email = module.invoker_sa.email
      audience              = module.reporter.uri
    }
  }

  depends_on = [module.services]
}

# ---------------- Alerta: mensajes en la dead letter ----------------
resource "google_monitoring_alert_policy" "dead_letter" {
  display_name = "${local.name} mensajes en dead letter"
  combiner     = "OR"

  conditions {
    display_name = "dead_letter_message_count > 0"
    condition_threshold {
      filter          = "resource.type = \"pubsub_subscription\" AND resource.labels.subscription_id = \"${google_pubsub_subscription.processor.name}\" AND metric.type = \"pubsub.googleapis.com/subscription/dead_letter_message_count\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = var.notification_channels

  documentation {
    content   = "Hay órdenes que fallaron ${var.max_delivery_attempts} veces. Revisa la suscripción ${google_pubsub_subscription.dead_letter_inspect.name}, corrige y re-publica."
    mime_type = "text/markdown"
  }
}
