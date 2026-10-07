output "answer_url" {
  value = module.answer_fn.uri
}

output "docs_bucket" {
  value = module.docs.name
}

output "data_store_id" {
  value = google_discovery_engine_data_store.docs.data_store_id
}

output "engine_id" {
  value = google_discovery_engine_search_engine.docs.engine_id
}

output "search_location" {
  value = var.search_location
}
