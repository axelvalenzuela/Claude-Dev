output "migration_job" {
  value = google_database_migration_service_migration_job.this.migration_job_id
}

output "source_host" {
  value = local.source_host
}

output "source_vm" {
  value = var.create_demo_source ? google_compute_instance.source[0].name : null
}

output "source_zone" {
  value = var.create_demo_source ? google_compute_instance.source[0].zone : null
}

output "destination_profile" {
  value = google_database_migration_service_connection_profile.destination.connection_profile_id
}
