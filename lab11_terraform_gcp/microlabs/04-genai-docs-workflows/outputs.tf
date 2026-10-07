output "documents_bucket" {
  value = module.documents.name
}

output "workflow" {
  value = google_workflows_workflow.pipeline.name
}

output "results_table" {
  value = "${var.project_id}.${google_bigquery_table.documents.dataset_id}.${google_bigquery_table.documents.table_id}"
}
