output "gateway_url" {
  value = "https://${google_api_gateway_gateway.this.default_hostname}"
}

output "api_key" {
  description = "terraform output -raw api_key"
  value       = google_apikeys_key.client.key_string
  sensitive   = true
}

output "function_uri" {
  description = "URL directa de la función (debe rechazar llamadas sin ID token del gateway)."
  value       = module.items_fn.uri
}

output "function_service_name" {
  description = "Servicio de Cloud Run subyacente (lo usa el micro lab 07 para el SLO)."
  value       = module.items_fn.service_name
}

output "firestore_database" {
  value = google_firestore_database.items.name
}
