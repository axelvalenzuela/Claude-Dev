output "topic" {
  value = google_pubsub_topic.orders.name
}

output "high_value_subscription" {
  value = google_pubsub_subscription.high_value.name
}

output "dead_letter_subscription" {
  value = google_pubsub_subscription.dead_letter_inspect.name
}

output "processor_subscription" {
  value = google_pubsub_subscription.processor.name
}

output "processor_function" {
  value = module.processor.name
}

output "audit_table" {
  value = "${var.project_id}.${google_bigquery_table.events.dataset_id}.${google_bigquery_table.events.table_id}"
}

output "scheduler_job" {
  value = google_cloud_scheduler_job.report.name
}
