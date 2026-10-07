output "service_url" {
  description = "Public URL of the Cloud Run service (open it in a browser to use the chat page)."
  value       = module.cloud_run.url
}

output "runtime_service_account" {
  value = module.service_account.email
}
