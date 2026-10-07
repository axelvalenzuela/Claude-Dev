output "events_topic" {
  value = google_pubsub_topic.events.name
}

output "raw_table" {
  value = "${var.project_id}.${google_bigquery_table.events.dataset_id}.${google_bigquery_table.events.table_id}"
}

output "kpi_table" {
  value = "${var.project_id}.${google_bigquery_table.daily_kpis.dataset_id}.${google_bigquery_table.daily_kpis.table_id}"
}

output "shared_view" {
  value = "${var.project_id}.${google_bigquery_table.v_kpis.dataset_id}.${google_bigquery_table.v_kpis.table_id}"
}

output "transfer_config" {
  value = google_bigquery_data_transfer_config.daily_kpis.name
}

output "dlq_subscription" {
  value = google_pubsub_subscription.dlq_inspect.name
}
