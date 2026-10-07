# Micro lab 08 (GCP) - Analítica con BigQuery (data platform mínima)
#   Ingesta streaming sin código: Pub/Sub -> suscripción BigQuery (use_table_schema)
#   raw.events: particionada por día + clustering + require_partition_filter (control de costo)
#   curated.daily_kpis: MERGE diario con scheduled query (Data Transfer Service)
#   shared.v_kpis: vista AUTORIZADA para analistas (sin acceso a datos crudos ni a columnas sensibles)

data "google_project" "this" {}

locals {
  name           = "lab11_${var.environment}_bq"
  pubsub_service = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"

  common_labels = {
    project     = "lab11"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "08-bigquery-analytics"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services   = ["bigquery.googleapis.com", "bigquerydatatransfer.googleapis.com", "pubsub.googleapis.com"]
}

# ---------------- Datasets por capa ----------------
resource "google_bigquery_dataset" "raw" {
  dataset_id                      = "${local.name}_raw"
  location                        = var.bq_location
  description                     = "Datos crudos (acceso restringido)"
  delete_contents_on_destroy      = true
  default_partition_expiration_ms = var.raw_retention_days * 86400000
  depends_on                      = [module.services]
}

resource "google_bigquery_dataset" "curated" {
  dataset_id                 = "${local.name}_curated"
  location                   = var.bq_location
  description                = "KPIs agregados"
  delete_contents_on_destroy = true
  depends_on                 = [module.services]
}

resource "google_bigquery_dataset" "shared" {
  dataset_id                 = "${local.name}_shared"
  location                   = var.bq_location
  description                = "Vistas autorizadas para analistas"
  delete_contents_on_destroy = true
  depends_on                 = [module.services]
}

# ---------------- Tablas ----------------
resource "google_bigquery_table" "events" {
  dataset_id               = google_bigquery_dataset.raw.dataset_id
  table_id                 = "events"
  deletion_protection      = false
  require_partition_filter = true # consultas sin filtro de fecha fallan (evita escanear todo)
  clustering               = ["country", "event_type"]

  time_partitioning {
    type  = "DAY"
    field = "event_ts"
  }

  schema = file("${path.module}/schemas/events.json")
}

resource "google_bigquery_table" "daily_kpis" {
  dataset_id          = google_bigquery_dataset.curated.dataset_id
  table_id            = "daily_kpis"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "day"
  }

  schema = jsonencode([
    { name = "day", type = "DATE", mode = "REQUIRED" },
    { name = "country", type = "STRING", mode = "REQUIRED" },
    { name = "event_type", type = "STRING", mode = "REQUIRED" },
    { name = "events", type = "INT64", mode = "NULLABLE" },
    { name = "unique_users", type = "INT64", mode = "NULLABLE" },
    { name = "revenue", type = "NUMERIC", mode = "NULLABLE" },
  ])
}

# Vista autorizada: agrega y NO expone user_id ni email
resource "google_bigquery_table" "v_kpis" {
  dataset_id          = google_bigquery_dataset.shared.dataset_id
  table_id            = "v_kpis"
  deletion_protection = false

  view {
    use_legacy_sql = false
    query          = <<-SQL
      SELECT day, country, event_type, events, unique_users, revenue
      FROM `${var.project_id}.${google_bigquery_dataset.curated.dataset_id}.${google_bigquery_table.daily_kpis.table_id}`
      WHERE day >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    SQL
  }
}

resource "google_bigquery_dataset_access" "authorized_view" {
  dataset_id = google_bigquery_dataset.curated.dataset_id
  view {
    project_id = var.project_id
    dataset_id = google_bigquery_dataset.shared.dataset_id
    table_id   = google_bigquery_table.v_kpis.table_id
  }
}

# Analistas: solo leen el dataset compartido y ejecutan jobs
resource "google_bigquery_dataset_iam_member" "analysts" {
  for_each   = toset(var.analyst_members)
  dataset_id = google_bigquery_dataset.shared.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = each.value
}

resource "google_project_iam_member" "analysts_jobs" {
  for_each = toset(var.analyst_members)
  project  = var.project_id
  role     = "roles/bigquery.jobUser"
  member   = each.value
}

# ---------------- Ingesta streaming: Pub/Sub -> BigQuery ----------------
resource "google_pubsub_topic" "events" {
  name       = "${replace(local.name, "_", "-")}-events"
  depends_on = [module.services]
}

resource "google_bigquery_dataset_iam_member" "pubsub_writer" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = local.pubsub_service
}

resource "google_pubsub_topic" "ingest_dead_letter" {
  name       = "${replace(local.name, "_", "-")}-ingest-dlq"
  depends_on = [module.services]
}

resource "google_pubsub_topic_iam_member" "dlq_publisher" {
  topic  = google_pubsub_topic.ingest_dead_letter.id
  role   = "roles/pubsub.publisher"
  member = local.pubsub_service
}

resource "google_pubsub_subscription" "to_bigquery" {
  name  = "${replace(local.name, "_", "-")}-to-bq"
  topic = google_pubsub_topic.events.id

  bigquery_config {
    table               = "${var.project_id}.${google_bigquery_table.events.dataset_id}.${google_bigquery_table.events.table_id}"
    use_table_schema    = true # el JSON del mensaje se mapea a columnas
    drop_unknown_fields = true
  }

  # Mensajes que no encajan con el esquema van a la DLQ en lugar de perderse
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.ingest_dead_letter.id
    max_delivery_attempts = 5
  }

  expiration_policy {
    ttl = ""
  }

  depends_on = [google_bigquery_dataset_iam_member.pubsub_writer]
}

resource "google_pubsub_subscription_iam_member" "dlq_subscriber" {
  subscription = google_pubsub_subscription.to_bigquery.id
  role         = "roles/pubsub.subscriber"
  member       = local.pubsub_service
}

resource "google_pubsub_subscription" "dlq_inspect" {
  name  = "${replace(local.name, "_", "-")}-ingest-dlq-inspect"
  topic = google_pubsub_topic.ingest_dead_letter.id
  expiration_policy {
    ttl = ""
  }
}

# ---------------- Transformación: scheduled query ----------------
module "transfer_sa" {
  source        = "../../modules/service-account"
  project_id    = var.project_id
  account_id    = "lab11-${var.environment}-bq-sched"
  display_name  = "Scheduled queries del lab 08"
  project_roles = ["roles/bigquery.jobUser"]
  depends_on    = [module.services]
}

resource "google_bigquery_dataset_iam_member" "transfer_reads_raw" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = module.transfer_sa.member
}

resource "google_bigquery_dataset_iam_member" "transfer_writes_curated" {
  dataset_id = google_bigquery_dataset.curated.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = module.transfer_sa.member
}

resource "google_bigquery_data_transfer_config" "daily_kpis" {
  display_name         = "${local.name} daily KPIs"
  location             = var.bq_location
  data_source_id       = "scheduled_query"
  schedule             = var.kpi_schedule
  service_account_name = module.transfer_sa.email

  params = {
    query = templatefile("${path.module}/sql/merge_daily_kpis.sql.tpl", {
      raw_table     = "${var.project_id}.${google_bigquery_table.events.dataset_id}.${google_bigquery_table.events.table_id}"
      curated_table = "${var.project_id}.${google_bigquery_table.daily_kpis.dataset_id}.${google_bigquery_table.daily_kpis.table_id}"
    })
  }

  depends_on = [
    google_bigquery_dataset_iam_member.transfer_reads_raw,
    google_bigquery_dataset_iam_member.transfer_writes_curated,
  ]
}
