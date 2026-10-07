output "dashboard_url" {
  value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards/dashboard/${aws_cloudwatch_dashboard.sre.dashboard_name}"
}

output "alerts_topic_arn" {
  value = module.alerts.topic_arn
}

output "error_budget_minutes_per_30d" {
  value = floor((1 - var.slo_target) * 30 * 24 * 60)
}

output "fis_template_id" {
  value = var.enable_fis ? aws_fis_experiment_template.stop_instance[0].id : null
}
