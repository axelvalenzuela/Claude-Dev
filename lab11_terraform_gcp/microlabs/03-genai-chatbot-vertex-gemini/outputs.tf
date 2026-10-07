output "chat_url" {
  value = module.chat_fn.uri
}

output "service_name" {
  value = module.chat_fn.service_name
}

output "firestore_database" {
  value = google_firestore_database.history.name
}
