output "app_url" {
  value = "http://${google_compute_global_address.lb.address}"
}

output "mig_name" {
  value = google_compute_region_instance_group_manager.app.name
}

output "backend_service" {
  value = google_compute_backend_service.app.name
}

output "db_instance" {
  value = google_sql_database_instance.db.name
}

output "db_private_ip" {
  value = google_sql_database_instance.db.private_ip_address
}
