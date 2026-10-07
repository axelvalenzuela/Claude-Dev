output "name" {
  value = google_cloudfunctions2_function.this.name
}

output "uri" {
  value = google_cloudfunctions2_function.this.service_config[0].uri
}

output "service_name" {
  description = "Nombre del servicio de Cloud Run subyacente (métricas run.googleapis.com/*)."
  value       = google_cloudfunctions2_function.this.name
}

output "id" {
  value = google_cloudfunctions2_function.this.id
}
