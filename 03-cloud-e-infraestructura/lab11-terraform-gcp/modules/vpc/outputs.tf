output "network_id" {
  value = google_compute_network.this.id
}

output "network_name" {
  value = google_compute_network.this.name
}

output "network_self_link" {
  value = google_compute_network.this.self_link
}

output "subnet_ids" {
  value = { for k, s in google_compute_subnetwork.this : k => s.id }
}

output "subnet_self_links" {
  value = { for k, s in google_compute_subnetwork.this : k => s.self_link }
}

output "subnet_names" {
  value = { for k, s in google_compute_subnetwork.this : k => s.name }
}

output "psa_connection" {
  description = "Úsalo en depends_on de Cloud SQL con IP privada."
  value       = try(google_service_networking_connection.psa[0].id, null)
}
