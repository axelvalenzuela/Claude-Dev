output "bucket" {
  description = "Bucket de trabajo (GCS_BUCKET en 04-vertex-ai-projects/.env)"
  value       = google_storage_bucket.migracion.name
}

output "dataset" {
  description = "Dataset de BigQuery (BQ_DATASET en 04-vertex-ai-projects/.env)"
  value       = google_bigquery_dataset.migracion.dataset_id
}

output "cuenta_servicio" {
  description = "Cuenta de servicio que usan la Function y Cloud Run"
  value       = google_service_account.agente.email
}

output "siguientes_pasos" {
  value = <<-EOT
    1. En 04-vertex-ai-projects/.env pon: MODO=real, GCP_PROJECT_ID=${var.proyecto}, GCS_BUCKET=${google_storage_bucket.migracion.name}
    2. python 10_setup_gcp/verificar_entorno.py
    3. python 17_bigquery/sas_a_bigquery.py
  EOT
}
