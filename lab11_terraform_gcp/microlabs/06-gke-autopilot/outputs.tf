output "cluster_name" {
  value = google_container_cluster.this.name
}

output "get_credentials" {
  value = "gcloud container clusters get-credentials ${google_container_cluster.this.name} --region ${var.region} --project ${var.project_id}"
}

output "namespace" {
  value = local.namespace
}

output "app_ip" {
  value = try(kubernetes_service_v1.app.status[0].load_balancer[0].ingress[0].ip, "pendiente")
}
