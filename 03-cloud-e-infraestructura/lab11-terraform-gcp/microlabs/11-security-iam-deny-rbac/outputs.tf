output "log_bucket" {
  value = google_logging_project_bucket_config.audit.id
}

output "archive_bucket" {
  value = module.archive.name
}

output "deny_policy" {
  value = google_iam_deny_policy.guardrails.name
}

output "probe_service_account" {
  value = module.probe_sa.email
}

output "custom_role" {
  value = google_project_iam_custom_role.deployer.id
}

output "rbac_bindings" {
  value = keys(local.rbac_bindings)
}
