# Micro lab 07 (GCP) - SRE con Cloud Monitoring
#   Servicio + SLOs (disponibilidad y latencia) request-based sobre la función del micro lab 01 (Cloud Run)
#   Alertas por burn rate multi-window (select_slo_burn_rate) · uptime check · dashboard · métrica de logs

data "terraform_remote_state" "api" {
  count   = var.api_state_bucket == null ? 0 : 1
  backend = "gcs"
  config = {
    bucket = var.api_state_bucket
    prefix = "06-terraform-gcp/01-serverless-apigw-functions-firestore/${var.environment}"
  }
}

locals {
  name           = "aie-${var.environment}-sre"
  run_service    = try(data.terraform_remote_state.api[0].outputs.function_service_name, var.run_service_name)
  uptime_host    = try(trimprefix(data.terraform_remote_state.api[0].outputs.gateway_url, "https://"), var.uptime_host)
  run_filter     = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${local.run_service}\""
  slo_avail_name = "projects/${var.project_id}/services/${google_monitoring_custom_service.api.service_id}/serviceLevelObjectives/${google_monitoring_slo.availability.slo_id}"

  # Multi-window, multi-burn-rate (Google SRE Workbook)
  burn_alerts = {
    fast = { long = "3600s", short = "300s", rate = 14.4, severity = "CRITICAL" }
    slow = { long = "21600s", short = "1800s", rate = 6, severity = "WARNING" }
  }

  common_labels = {
    project     = "aie"
    environment = var.environment
    owner       = var.owner
    cost_center = var.cost_center
    managed_by  = "terraform"
    microlab    = "07-sre-slo-monitoring"
  }
}

module "services" {
  source     = "../../modules/project-services"
  project_id = var.project_id
  services   = ["monitoring.googleapis.com", "logging.googleapis.com"]
}

resource "google_monitoring_notification_channel" "email" {
  for_each     = toset(var.alert_emails)
  display_name = "06-terraform-gcp SRE ${each.value}"
  type         = "email"
  labels = {
    email_address = each.value
  }
  depends_on = [module.services]
}

# ---------------- Servicio y SLOs ----------------
resource "google_monitoring_custom_service" "api" {
  service_id   = "${local.name}-api"
  display_name = "06-terraform-gcp API de items (${local.run_service})"
  depends_on   = [module.services]
}

resource "google_monitoring_slo" "availability" {
  service             = google_monitoring_custom_service.api.service_id
  slo_id              = "availability"
  display_name        = "Disponibilidad ${var.availability_goal * 100}% (28 días)"
  goal                = var.availability_goal
  rolling_period_days = 28

  request_based_sli {
    good_total_ratio {
      bad_service_filter   = "${local.run_filter} AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\""
      total_service_filter = "${local.run_filter} AND metric.type=\"run.googleapis.com/request_count\""
    }
  }
}

resource "google_monitoring_slo" "latency" {
  service             = google_monitoring_custom_service.api.service_id
  slo_id              = "latency"
  display_name        = "${var.latency_goal * 100}% de requests < ${var.latency_threshold_ms} ms"
  goal                = var.latency_goal
  rolling_period_days = 28

  request_based_sli {
    distribution_cut {
      distribution_filter = "${local.run_filter} AND metric.type=\"run.googleapis.com/request_latencies\""
      range {
        max = var.latency_threshold_ms
      }
    }
  }
}

# ---------------- Alertas por burn rate ----------------
resource "google_monitoring_alert_policy" "burn" {
  for_each     = local.burn_alerts
  display_name = "${local.name} SLO burn ${each.key} (${each.value.rate}x)"
  combiner     = "AND" # ventana larga Y corta: detecta rápido y se resetea rápido
  severity     = each.value.severity

  conditions {
    display_name = "burn rate ${each.value.long}"
    condition_threshold {
      filter          = "select_slo_burn_rate(\"${local.slo_avail_name}\", \"${each.value.long}\")"
      comparison      = "COMPARISON_GT"
      threshold_value = each.value.rate
      duration        = "0s"
    }
  }

  conditions {
    display_name = "burn rate ${each.value.short}"
    condition_threshold {
      filter          = "select_slo_burn_rate(\"${local.slo_avail_name}\", \"${each.value.short}\")"
      comparison      = "COMPARISON_GT"
      threshold_value = each.value.rate
      duration        = "0s"
    }
  }

  notification_channels = [for c in google_monitoring_notification_channel.email : c.id]

  documentation {
    content   = "El SLO de disponibilidad consume presupuesto a ${each.value.rate}x. Runbook: ${var.runbook_url}"
    mime_type = "text/markdown"
  }
}

# ---------------- Caja negra: uptime check ----------------
resource "google_monitoring_uptime_check_config" "health" {
  display_name     = "${local.name} /health"
  timeout          = "10s"
  period           = "60s"
  checker_type     = "STATIC_IP_CHECKERS"
  selected_regions = ["USA_OREGON", "USA_IOWA", "USA_VIRGINIA"]

  http_check {
    path         = "/health"
    port         = 443
    use_ssl      = true
    validate_ssl = true
    accepted_response_status_codes {
      status_class = "STATUS_CLASS_2XX"
    }
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = local.uptime_host
    }
  }

  depends_on = [module.services]
}

resource "google_monitoring_alert_policy" "uptime" {
  display_name = "${local.name} uptime /health"
  combiner     = "OR"
  severity     = "ERROR"

  conditions {
    display_name = "Uptime falla en 2+ regiones"
    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.labels.check_id=\"${google_monitoring_uptime_check_config.health.uptime_check_id}\" AND resource.type=\"uptime_url\""
      comparison      = "COMPARISON_GT"
      threshold_value = 1
      duration        = "120s"
      aggregations {
        alignment_period     = "120s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        group_by_fields      = ["resource.label.*"]
      }
    }
  }

  notification_channels = [for c in google_monitoring_notification_channel.email : c.id]
}

# ---------------- Métrica basada en logs: fallas inyectadas / errores ----------------
resource "google_logging_metric" "app_errors" {
  name   = "${local.name}/app_errors"
  filter = "${local.run_filter} AND severity>=ERROR"
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
  depends_on = [module.services]
}

# ---------------- Dashboard ----------------
resource "google_monitoring_dashboard" "golden_signals" {
  dashboard_json = templatefile("${path.module}/dashboard.json.tpl", {
    title       = "06-terraform-gcp golden signals - ${local.run_service}"
    run_service = local.run_service
    slo_name    = local.slo_avail_name
    uptime_id   = google_monitoring_uptime_check_config.health.uptime_check_id
  })
  depends_on = [module.services]
}
