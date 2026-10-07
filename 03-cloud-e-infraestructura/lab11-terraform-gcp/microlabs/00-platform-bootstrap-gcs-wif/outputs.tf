output "tf_state_bucket" {
  description = "Variable de GitLab TF_STATE_BUCKET."
  value       = module.state_bucket.name
}

output "wif_provider" {
  description = "Variable de GitLab GCP_WIF_PROVIDER."
  value       = google_iam_workload_identity_pool_provider.gitlab.name
}

output "plan_service_account" {
  description = "Variable de GitLab GCP_PLAN_SA."
  value       = module.plan_sa.email
}

output "apply_service_account" {
  description = "Variable de GitLab GCP_APPLY_SA (protegida)."
  value       = module.apply_sa.email
}

output "build_service_account" {
  description = "Úsalo como build_service_account en los labs con Cloud Run functions."
  value       = module.builder_sa.id
}

output "artifact_registry" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.containers.repository_id}"
}

output "project_number" {
  value = data.google_project.this.number
}
