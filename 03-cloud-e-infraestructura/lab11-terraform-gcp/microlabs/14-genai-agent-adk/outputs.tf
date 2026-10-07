output "agent_url" {
  value = module.agent_fn.uri
}

output "firestore_database" {
  value = google_firestore_database.store.name
}
