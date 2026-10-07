# Micro lab 07 - SRE: SLOs, alertas por burn rate, monitoreo sintético, ChatOps y Chaos Engineering
#   Observa la API del micro lab 01 y el ASG del micro lab 06 (o cualquier recurso equivalente).

data "aws_caller_identity" "current" {}

# Si se indica el bucket de estado, toma los datos del API directamente de los outputs del lab 01
# (evita copiar nombres/URLs a mano y mantiene ambos labs sincronizados).
data "terraform_remote_state" "lab01" {
  count   = var.lab01_state_bucket == null ? 0 : 1
  backend = "s3"
  config = {
    bucket = var.lab01_state_bucket
    key    = "lab10_terraform_aws/01-serverless-apigw-lambda-dynamodb/${var.environment}.tfstate"
    region = var.aws_region
  }
}

locals {
  api_name             = try(data.terraform_remote_state.lab01[0].outputs.api_name, var.api_name)
  api_stage            = try(data.terraform_remote_state.lab01[0].outputs.stage_name, var.api_stage)
  api_access_log_group = try(data.terraform_remote_state.lab01[0].outputs.access_log_group, var.api_access_log_group)
  health_check_url     = try("${data.terraform_remote_state.lab01[0].outputs.api_url}/health", var.health_check_url)
}

locals {
  name = "${var.project}-${var.environment}-sre"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
    MicroLab    = "07-sre-slo-cloudwatch-fis"
  }

  error_budget = 1 - var.slo_target # p. ej. 0.001 para 99.9 %

  # Ventanas multi-window / multi-burn-rate (Google SRE Workbook, cap. 5)
  burn_windows = {
    fast = { long_period = 3600, short_period = 300, burn_rate = 14.4, severity = "page" }  # 2 % del presupuesto en 1 h
    slow = { long_period = 21600, short_period = 1800, burn_rate = 6, severity = "ticket" } # 5 % del presupuesto en 6 h
  }

  api_dimensions = {
    ApiName = local.api_name
    Stage   = local.api_stage
  }
}

module "kms" {
  source             = "../../modules/kms-key"
  alias              = local.name
  service_principals = ["cloudwatch.amazonaws.com", "events.amazonaws.com", "sns.amazonaws.com"]
}

module "alerts" {
  source              = "../../modules/sns-alerts"
  name                = "${local.name}-alerts"
  kms_key_arn         = module.kms.key_arn
  email_subscriptions = var.alert_emails
}

# ---------------------------------------------------------------------------
# SLO de disponibilidad: error_rate = 5XX / Count  vs  burn_rate × error_budget
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "burn_long" {
  for_each            = local.burn_windows
  alarm_name          = "${local.name}-slo-burn-${each.key}-long"
  alarm_description   = "Error rate en ventana larga > ${each.value.burn_rate}x presupuesto"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = each.value.burn_rate * local.error_budget
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "error_rate"
    expression  = "IF(requests > 0, errors / requests, 0)"
    label       = "Error rate"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      namespace   = "AWS/ApiGateway"
      metric_name = "5XXError"
      period      = each.value.long_period
      stat        = "Sum"
      dimensions  = local.api_dimensions
    }
  }

  metric_query {
    id = "requests"
    metric {
      namespace   = "AWS/ApiGateway"
      metric_name = "Count"
      period      = each.value.long_period
      stat        = "Sum"
      dimensions  = local.api_dimensions
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "burn_short" {
  for_each            = local.burn_windows
  alarm_name          = "${local.name}-slo-burn-${each.key}-short"
  alarm_description   = "Error rate en ventana corta > ${each.value.burn_rate}x presupuesto"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = each.value.burn_rate * local.error_budget
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "error_rate"
    expression  = "IF(requests > 0, errors / requests, 0)"
    label       = "Error rate"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      namespace   = "AWS/ApiGateway"
      metric_name = "5XXError"
      period      = each.value.short_period
      stat        = "Sum"
      dimensions  = local.api_dimensions
    }
  }

  metric_query {
    id = "requests"
    metric {
      namespace   = "AWS/ApiGateway"
      metric_name = "Count"
      period      = each.value.short_period
      stat        = "Sum"
      dimensions  = local.api_dimensions
    }
  }
}

# Alerta solo si AMBAS ventanas arden: rápida detección y reseteo, pocos falsos positivos.
resource "aws_cloudwatch_composite_alarm" "slo_burn" {
  for_each          = local.burn_windows
  alarm_name        = "${local.name}-slo-${each.key}-burn-${each.value.severity}"
  alarm_description = "SLO ${var.slo_target * 100}% consumiendo presupuesto a ${each.value.burn_rate}x. Runbook: ${var.runbook_url}"
  alarm_rule        = "ALARM(\"${aws_cloudwatch_metric_alarm.burn_long[each.key].alarm_name}\") AND ALARM(\"${aws_cloudwatch_metric_alarm.burn_short[each.key].alarm_name}\")"
  alarm_actions     = [module.alerts.topic_arn]
  ok_actions        = [module.alerts.topic_arn]
}

# SLO de latencia: p99 < umbral
resource "aws_cloudwatch_metric_alarm" "latency_slo" {
  alarm_name          = "${local.name}-slo-latency-p99"
  namespace           = "AWS/ApiGateway"
  metric_name         = "Latency"
  extended_statistic  = "p99"
  period              = 300
  evaluation_periods  = 3
  datapoints_to_alarm = 2
  threshold           = var.latency_p99_ms
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions          = local.api_dimensions
  alarm_actions       = [module.alerts.topic_arn]
}

# ---------------------------------------------------------------------------
# Monitoreo sintético (caja negra): CloudWatch Synthetics
# ---------------------------------------------------------------------------
module "canary_artifacts" {
  source          = "../../modules/s3-secure-bucket"
  bucket_name     = "${local.name}-canary-${data.aws_caller_identity.current.account_id}"
  expiration_days = 14
}

data "archive_file" "canary" {
  type        = "zip"
  source_dir  = "${path.module}/canary"
  output_path = "${path.module}/.build/canary.zip"
}

data "aws_iam_policy_document" "canary_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "canary" {
  name               = "${local.name}-canary"
  assume_role_policy = data.aws_iam_policy_document.canary_assume.json
}

data "aws_iam_policy_document" "canary" {
  statement {
    actions   = ["s3:PutObject", "s3:GetObject"]
    resources = ["${module.canary_artifacts.bucket_arn}/*"]
  }
  statement {
    actions   = ["s3:GetBucketLocation", "s3:ListAllMyBuckets"]
    resources = ["*"]
  }
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/cwsyn-*"]
  }
  statement {
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["CloudWatchSynthetics"]
    }
  }
  statement {
    actions   = ["xray:PutTraceSegments"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "canary" {
  name   = "canary"
  role   = aws_iam_role.canary.id
  policy = data.aws_iam_policy_document.canary.json
}

resource "aws_synthetics_canary" "health" {
  name                 = substr(replace("${var.environment}-api-health", "_", "-"), 0, 21)
  artifact_s3_location = "s3://${module.canary_artifacts.bucket_id}/canary/"
  execution_role_arn   = aws_iam_role.canary.arn
  runtime_version      = var.canary_runtime_version
  handler              = "index.handler"
  zip_file             = data.archive_file.canary.output_path
  start_canary         = true

  schedule {
    expression = "rate(5 minutes)"
  }

  run_config {
    timeout_in_seconds = 60
    active_tracing     = true
    environment_variables = {
      TARGET_URL = local.health_check_url
    }
  }

  success_retention_period = 7
  failure_retention_period = 14
}

resource "aws_cloudwatch_metric_alarm" "canary" {
  alarm_name          = "${local.name}-canary-success"
  namespace           = "CloudWatchSynthetics"
  metric_name         = "SuccessPercent"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 90
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"
  alarm_actions       = [module.alerts.topic_arn]
  dimensions = {
    CanaryName = aws_synthetics_canary.health.name
  }
}

# ---------------------------------------------------------------------------
# Dashboard y consultas guardadas
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_dashboard" "sre" {
  dashboard_name = "${local.name}-golden-signals"
  dashboard_body = templatefile("${path.module}/dashboard.json.tpl", {
    region     = var.aws_region
    api_name   = local.api_name
    api_stage  = local.api_stage
    canary     = aws_synthetics_canary.health.name
    slo_target = var.slo_target
  })
}

resource "aws_cloudwatch_query_definition" "api_errors" {
  name            = "${local.name}/api-5xx-por-ruta"
  log_group_names = [local.api_access_log_group]
  query_string    = <<-EOT
    fields @timestamp, httpMethod, resourcePath, status, latency, integrationErr
    | filter status >= 500
    | stats count(*) as errores by resourcePath, status
    | sort errores desc
  EOT
}

# ---------------------------------------------------------------------------
# ChatOps: Amazon Q Developer in chat applications (antes AWS Chatbot) -> Slack
# Requiere autorizar el workspace de Slack una vez en la consola.
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "chatbot_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["chatbot.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "chatbot" {
  count              = var.slack_team_id == "" ? 0 : 1
  name               = "${local.name}-chatbot"
  assume_role_policy = data.aws_iam_policy_document.chatbot_assume.json
}

resource "aws_iam_role_policy_attachment" "chatbot" {
  count      = var.slack_team_id == "" ? 0 : 1
  role       = aws_iam_role.chatbot[0].name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
}

resource "aws_chatbot_slack_channel_configuration" "oncall" {
  count                 = var.slack_team_id == "" ? 0 : 1
  configuration_name    = "${local.name}-oncall"
  iam_role_arn          = aws_iam_role.chatbot[0].arn
  slack_team_id         = var.slack_team_id
  slack_channel_id      = var.slack_channel_id
  sns_topic_arns        = [module.alerts.topic_arn]
  guardrail_policy_arns = ["arn:aws:iam::aws:policy/ReadOnlyAccess"]
  logging_level         = "ERROR"
}

# ---------------------------------------------------------------------------
# Chaos Engineering: AWS Fault Injection Service (opcional)
# Detiene 1 instancia con la etiqueta indicada; se aborta si la alarma de stop salta.
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "fis_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["fis.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "fis" {
  count              = var.enable_fis ? 1 : 0
  name               = "${local.name}-fis"
  assume_role_policy = data.aws_iam_policy_document.fis_assume.json
}

resource "aws_iam_role_policy" "fis" {
  count = var.enable_fis ? 1 : 0
  name  = "stop-tagged-instances"
  role  = aws_iam_role.fis[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Action    = ["ec2:StopInstances", "ec2:StartInstances"]
        Resource  = "arn:aws:ec2:*:*:instance/*"
        Condition = { StringEquals = { "aws:ResourceTag/${var.fis_target_tag_key}" = var.fis_target_tag_value } }
      },
      {
        Effect   = "Allow"
        Action   = ["ec2:DescribeInstances"]
        Resource = "*"
      },
    ]
  })
}

resource "aws_fis_experiment_template" "stop_instance" {
  count       = var.enable_fis ? 1 : 0
  description = "GameDay: detener 1 instancia de la capa app y verificar autorecuperación"
  role_arn    = aws_iam_role.fis[0].arn

  stop_condition {
    source = "aws:cloudwatch:alarm"
    value  = aws_cloudwatch_metric_alarm.canary.arn
  }

  action {
    name      = "stop-one-instance"
    action_id = "aws:ec2:stop-instances"

    parameter {
      key   = "startInstancesAfterDuration"
      value = "PT5M"
    }

    target {
      key   = "Instances"
      value = "app-instances"
    }
  }

  target {
    name           = "app-instances"
    resource_type  = "aws:ec2:instance"
    selection_mode = "COUNT(1)"

    resource_tag {
      key   = var.fis_target_tag_key
      value = var.fis_target_tag_value
    }

    filter {
      path   = "State.Name"
      values = ["running"]
    }
  }

  tags = { Name = "${local.name}-stop-instance" }
}
