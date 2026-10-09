output "services" {
  description = "Úsalo en depends_on para esperar a que las APIs estén listas."
  value       = [for s in google_project_service.this : s.service]
  depends_on  = [time_sleep.propagation]
}
