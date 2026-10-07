output "ask_url" {
  value = module.rag_fn.uri
}

output "dataset" {
  value = local.dataset
}

output "chunks_table" {
  value = "${var.project_id}.${local.dataset}.${google_bigquery_table.chunks.table_id}"
}

output "embedding_model" {
  value = "${var.project_id}.${local.dataset}.embedding_model"
}
