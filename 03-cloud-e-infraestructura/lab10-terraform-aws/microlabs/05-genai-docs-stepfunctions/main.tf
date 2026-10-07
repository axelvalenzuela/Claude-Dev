# Micro lab 05 - Pipeline de IA para documentos (serverless, orquestado)
#   S3 (incoming/) -> EventBridge "Object Created" -> Step Functions
#     -> Lambda extract (Textract) -> Parallel[Comprehend entities | Lambda summarize (Bedrock)]
#     -> DynamoDB resultados ; errores -> SNS

data "aws_caller_identity" "current" {}

locals {
  name = "${var.project}-${var.environment}-docai"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
    MicroLab    = "05-genai-docs-stepfunctions"
  }
}

module "kms" {
  source             = "../../modules/kms-key"
  alias              = local.name
  description        = "Cifrado de documentos y resultados"
  service_principals = ["sns.amazonaws.com", "events.amazonaws.com", "states.amazonaws.com"]
}

module "documents" {
  source                           = "../../modules/s3-secure-bucket"
  bucket_name                      = "${local.name}-docs-${data.aws_caller_identity.current.account_id}"
  kms_key_arn                      = module.kms.key_arn
  expiration_days                  = var.document_retention_days
  enable_eventbridge_notifications = true
}

module "results" {
  source   = "../../modules/dynamodb-table"
  name     = "${local.name}-results"
  hash_key = "document_id"
}

module "alerts" {
  source              = "../../modules/sns-alerts"
  name                = "${local.name}-alerts"
  kms_key_arn         = module.kms.key_arn
  email_subscriptions = var.alert_emails
}

# ---------------- Lambdas ----------------
data "aws_iam_policy_document" "extract" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${module.documents.bucket_arn}/incoming/*"]
  }
  statement {
    actions   = ["textract:DetectDocumentText"]
    resources = ["*"]
  }
  statement {
    actions   = ["kms:Decrypt"]
    resources = [module.kms.key_arn]
  }
}

module "extract_fn" {
  source               = "../../modules/lambda-function"
  function_name        = "${local.name}-extract"
  source_dir           = "${path.module}/src/extract"
  timeout              = 60
  memory_size          = 512
  attach_inline_policy = true
  inline_policy_json   = data.aws_iam_policy_document.extract.json
}

data "aws_iam_policy_document" "summarize" {
  statement {
    actions = ["bedrock:InvokeModel"]
    resources = [
      "arn:aws:bedrock:*::foundation-model/*",
      "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/*",
    ]
  }
}

module "summarize_fn" {
  source               = "../../modules/lambda-function"
  function_name        = "${local.name}-summarize"
  source_dir           = "${path.module}/src/summarize"
  timeout              = 60
  memory_size          = 256
  reserved_concurrency = 5
  attach_inline_policy = true
  inline_policy_json   = data.aws_iam_policy_document.summarize.json
  environment = {
    MODEL_ID   = var.model_id
    MAX_TOKENS = "300"
  }
}

# ---------------- Step Functions ----------------
data "aws_iam_policy_document" "sfn_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_iam_role" "sfn" {
  name               = "${local.name}-sfn"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume.json
}

data "aws_iam_policy_document" "sfn" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [module.extract_fn.function_arn, module.summarize_fn.function_arn]
  }
  statement {
    actions   = ["comprehend:DetectEntities"]
    resources = ["*"]
  }
  statement {
    actions   = ["dynamodb:PutItem"]
    resources = [module.results.table_arn]
  }
  statement {
    actions   = ["sns:Publish"]
    resources = [module.alerts.topic_arn]
  }
  statement {
    actions   = ["kms:GenerateDataKey", "kms:Decrypt"]
    resources = [module.kms.key_arn]
  }
  statement {
    sid = "LogsDelivery"
    actions = [
      "logs:CreateLogDelivery", "logs:GetLogDelivery", "logs:UpdateLogDelivery", "logs:DeleteLogDelivery",
      "logs:ListLogDeliveries", "logs:PutResourcePolicy", "logs:DescribeResourcePolicies", "logs:DescribeLogGroups",
    ]
    resources = ["*"]
  }
  statement {
    actions   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords", "xray:GetSamplingRules", "xray:GetSamplingTargets"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "sfn" {
  name   = "pipeline"
  role   = aws_iam_role.sfn.id
  policy = data.aws_iam_policy_document.sfn.json
}

resource "aws_cloudwatch_log_group" "sfn" {
  name              = "/aws/vendedlogs/states/${local.name}"
  retention_in_days = 30
}

resource "aws_sfn_state_machine" "pipeline" {
  name     = "${local.name}-pipeline"
  role_arn = aws_iam_role.sfn.arn
  type     = "STANDARD"

  definition = templatefile("${path.module}/statemachine.asl.json.tpl", {
    extract_fn_arn   = module.extract_fn.function_arn
    summarize_fn_arn = module.summarize_fn.function_arn
    table_name       = module.results.table_name
    alerts_topic_arn = module.alerts.topic_arn
    language_code    = var.language_code
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn.arn}:*"
    include_execution_data = false # evita registrar el contenido de documentos (privacidad)
    level                  = "ERROR"
  }

  tracing_configuration {
    enabled = true
  }

  depends_on = [aws_iam_role_policy.sfn]
}

# ---------------- Disparador: S3 -> EventBridge -> Step Functions ----------------
resource "aws_cloudwatch_event_rule" "new_document" {
  name = "${local.name}-new-document"
  event_pattern = jsonencode({
    source        = ["aws.s3"]
    "detail-type" = ["Object Created"]
    detail = {
      bucket = { name = [module.documents.bucket_id] }
      object = { key = [{ prefix = "incoming/" }] }
    }
  })
}

data "aws_iam_policy_document" "events_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "events" {
  name               = "${local.name}-events-to-sfn"
  assume_role_policy = data.aws_iam_policy_document.events_assume.json
}

resource "aws_iam_role_policy" "events" {
  name = "start-pipeline"
  role = aws_iam_role.events.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "states:StartExecution"
      Resource = aws_sfn_state_machine.pipeline.arn
    }]
  })
}

resource "aws_cloudwatch_event_target" "pipeline" {
  rule     = aws_cloudwatch_event_rule.new_document.name
  arn      = aws_sfn_state_machine.pipeline.arn
  role_arn = aws_iam_role.events.arn
}

resource "aws_cloudwatch_metric_alarm" "executions_failed" {
  alarm_name          = "${local.name}-executions-failed"
  namespace           = "AWS/States"
  metric_name         = "ExecutionsFailed"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [module.alerts.topic_arn]
  dimensions = {
    StateMachineArn = aws_sfn_state_machine.pipeline.arn
  }
}
