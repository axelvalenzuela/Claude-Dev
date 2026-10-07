# Micro lab 03 - Arquitectura orientada a eventos con Amazon EventBridge
#   Bus custom "orders" + archive/replay + reglas con filtrado de contenido
#   Destinos: Lambda (con retry + DLQ), SQS (alto valor), CloudWatch Logs (auditoría)
#   EventBridge Scheduler para tareas programadas

data "aws_caller_identity" "current" {}

locals {
  name = "${var.project}-${var.environment}-evt"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
    MicroLab    = "03-eventbridge-event-driven"
  }
}

# ---------------- Bus ----------------
resource "aws_cloudwatch_event_bus" "orders" {
  name = "${local.name}-orders"
}

resource "aws_cloudwatch_event_archive" "orders" {
  name             = "${local.name}-orders-archive"
  event_source_arn = aws_cloudwatch_event_bus.orders.arn
  retention_days   = var.archive_retention_days
}

# Permite que otras cuentas publiquen en el bus (patrón hub-and-spoke).
data "aws_iam_policy_document" "bus" {
  count = length(var.producer_account_ids) > 0 ? 1 : 0
  statement {
    sid       = "AllowProducerAccounts"
    actions   = ["events:PutEvents"]
    resources = [aws_cloudwatch_event_bus.orders.arn]
    principals {
      type        = "AWS"
      identifiers = var.producer_account_ids
    }
  }
}

resource "aws_cloudwatch_event_bus_policy" "orders" {
  count          = length(var.producer_account_ids) > 0 ? 1 : 0
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  policy         = data.aws_iam_policy_document.bus[0].json
}

# ---------------- Colas ----------------
resource "aws_sqs_queue" "dlq" {
  name                      = "${local.name}-dlq"
  message_retention_seconds = 1209600 # 14 días
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "high_value" {
  name                       = "${local.name}-high-value-orders"
  visibility_timeout_seconds = 60
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 5
  })
}

# ---------------- Lambdas ----------------
data "aws_iam_policy_document" "processor" {
  statement {
    sid       = "OnFailureDestination"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.dlq.arn]
  }
}

module "processor" {
  source               = "../../modules/lambda-function"
  function_name        = "${local.name}-order-processor"
  description          = "Procesa eventos order.created"
  source_dir           = "${path.module}/src/processor"
  reserved_concurrency = 10
  attach_inline_policy = true
  inline_policy_json   = data.aws_iam_policy_document.processor.json
}

# EventBridge invoca Lambda de forma ASÍNCRONA: si el código falla, el reintento y el destino
# de falla los gestiona Lambda (la DLQ del target de EventBridge solo cubre fallas de entrega).
resource "aws_lambda_function_event_invoke_config" "processor" {
  function_name                = module.processor.function_name
  maximum_retry_attempts       = var.processor_async_retries
  maximum_event_age_in_seconds = 3600

  destination_config {
    on_failure {
      destination = aws_sqs_queue.dlq.arn
    }
  }
}

module "reporter" {
  source        = "../../modules/lambda-function"
  function_name = "${local.name}-reporter"
  description   = "Tarea programada por EventBridge Scheduler"
  source_dir    = "${path.module}/src/reporter"
}

# ---------------- Regla 1: order.created -> Lambda ----------------
resource "aws_cloudwatch_event_rule" "order_created" {
  name           = "${local.name}-order-created"
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  event_pattern = jsonencode({
    source        = ["com.lab10.orders"]
    "detail-type" = ["order.created"]
  })
}

resource "aws_cloudwatch_event_target" "processor" {
  rule           = aws_cloudwatch_event_rule.order_created.name
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  arn            = module.processor.function_arn

  retry_policy {
    maximum_event_age_in_seconds = 3600
    maximum_retry_attempts       = 3
  }

  dead_letter_config {
    arn = aws_sqs_queue.dlq.arn
  }
}

resource "aws_lambda_permission" "processor" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.processor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.order_created.arn
}

# ---------------- Regla 2: órdenes de alto valor -> SQS (filtrado numérico) ----------------
resource "aws_cloudwatch_event_rule" "high_value" {
  name           = "${local.name}-high-value"
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  event_pattern = jsonencode({
    source = ["com.lab10.orders"]
    detail = {
      amount = [{ numeric = [">=", var.high_value_threshold] }]
    }
  })
}

resource "aws_cloudwatch_event_target" "high_value" {
  rule           = aws_cloudwatch_event_rule.high_value.name
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  arn            = aws_sqs_queue.high_value.arn

  # Transforma el evento: el consumidor solo recibe lo que necesita.
  input_transformer {
    input_paths = {
      orderId = "$.detail.orderId"
      amount  = "$.detail.amount"
      time    = "$.time"
    }
    input_template = <<-EOT
      {"orderId": <orderId>, "amount": <amount>, "receivedAt": <time>, "priority": "HIGH"}
    EOT
  }

  dead_letter_config {
    arn = aws_sqs_queue.dlq.arn
  }
}

data "aws_iam_policy_document" "queues" {
  statement {
    sid       = "AllowEventBridgeHighValue"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.high_value.arn]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudwatch_event_rule.high_value.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "high_value" {
  queue_url = aws_sqs_queue.high_value.id
  policy    = data.aws_iam_policy_document.queues.json
}

data "aws_iam_policy_document" "dlq" {
  statement {
    sid       = "AllowEventBridgeDlq"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.dlq.arn]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values = [
        aws_cloudwatch_event_rule.order_created.arn,
        aws_cloudwatch_event_rule.high_value.arn,
      ]
    }
  }
}

resource "aws_sqs_queue_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id
  policy    = data.aws_iam_policy_document.dlq.json
}

# ---------------- Regla 3: auditoría de TODO el bus -> CloudWatch Logs ----------------
resource "aws_cloudwatch_log_group" "audit" {
  name              = "/aws/events/${local.name}-audit"
  retention_in_days = var.log_retention_days
}

data "aws_iam_policy_document" "logs" {
  statement {
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.audit.arn}:*"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com", "delivery.logs.amazonaws.com"]
    }
  }
}

resource "aws_cloudwatch_log_resource_policy" "events" {
  policy_name     = "${local.name}-events-to-logs"
  policy_document = data.aws_iam_policy_document.logs.json
}

resource "aws_cloudwatch_event_rule" "audit_all" {
  name           = "${local.name}-audit-all"
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  event_pattern = jsonencode({
    account = [data.aws_caller_identity.current.account_id]
  })
}

resource "aws_cloudwatch_event_target" "audit" {
  rule           = aws_cloudwatch_event_rule.audit_all.name
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  arn            = aws_cloudwatch_log_group.audit.arn
}

# ---------------- EventBridge Scheduler ----------------
data "aws_iam_policy_document" "scheduler_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "${local.name}-scheduler"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume.json
}

data "aws_iam_policy_document" "scheduler" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [module.reporter.function_arn]
  }
  statement {
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.dlq.arn]
  }
}

resource "aws_iam_role_policy" "scheduler" {
  name   = "invoke-reporter"
  role   = aws_iam_role.scheduler.id
  policy = data.aws_iam_policy_document.scheduler.json
}

resource "aws_scheduler_schedule" "reporter" {
  name                         = "${local.name}-hourly-report"
  schedule_expression          = var.report_schedule
  schedule_expression_timezone = var.schedule_timezone

  flexible_time_window {
    mode                      = "FLEXIBLE"
    maximum_window_in_minutes = 15
  }

  target {
    arn      = module.reporter.function_arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ report = "orders-summary" })

    retry_policy {
      maximum_retry_attempts = 2
    }

    dead_letter_config {
      arn = aws_sqs_queue.dlq.arn
    }
  }
}

# ---------------- Alarmas ----------------
resource "aws_cloudwatch_metric_alarm" "dlq_not_empty" {
  alarm_name          = "${local.name}-dlq-not-empty"
  alarm_description   = "Hay eventos que no pudieron entregarse: revisar y re-procesar"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  dimensions = {
    QueueName = aws_sqs_queue.dlq.name
  }
}

resource "aws_cloudwatch_metric_alarm" "failed_invocations" {
  alarm_name          = "${local.name}-failed-invocations"
  namespace           = "AWS/Events"
  metric_name         = "FailedInvocations"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    RuleName     = aws_cloudwatch_event_rule.order_created.name
    EventBusName = aws_cloudwatch_event_bus.orders.name
  }
}
