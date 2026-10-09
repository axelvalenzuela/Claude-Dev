output "root_folder" {
  value = google_folder.root.name
}

output "env_folders" {
  value = { for k, f in google_folder.env : k => f.name }
}

output "projects" {
  value = { for k, p in module.projects : k => p.project_id }
}

output "firewall_policy" {
  value = google_compute_firewall_policy.baseline.name
}
