output "dashboard_url" {
  value = "https://console.cloud.google.com/monitoring/dashboards/builder/${element(split("/", google_monitoring_dashboard.golden_signals.id), 3)}?project=${var.project_id}"
}

output "service_id" {
  value = google_monitoring_custom_service.api.service_id
}

output "availability_slo" {
  value = local.slo_avail_name
}

output "observed_service" {
  value = local.run_service
}

output "error_budget_minutes_28d" {
  value = floor((1 - var.availability_goal) * 28 * 24 * 60)
}
