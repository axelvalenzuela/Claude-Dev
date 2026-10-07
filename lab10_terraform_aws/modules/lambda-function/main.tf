# Módulo: función Lambda con buenas prácticas.
# - Rol IAM dedicado (mínimo privilegio) + políticas inline/administradas opcionales
# - Log group propio con retención y cifrado, logs en formato JSON
# - X-Ray activo, arquitectura arm64 (Graviton: mejor precio/rendimiento)
# - Concurrencia reservada, DLQ y VPC opcionales

data "archive_file" "this" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.root}/.build/${var.function_name}.zip"
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  name                 = "${var.function_name}-role"
  assume_role_policy   = data.aws_iam_policy_document.assume.json
  permissions_boundary = var.permissions_boundary_arn
  tags                 = var.tags
}

resource "aws_iam_role_policy_attachment" "basic" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "vpc" {
  count      = length(var.vpc_subnet_ids) > 0 ? 1 : 0
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "xray" {
  count      = var.tracing_mode == "Active" ? 1 : 0
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# Mapa con llaves estáticas para evitar errores de for_each con ARNs desconocidos en plan.
resource "aws_iam_role_policy_attachment" "extra" {
  for_each   = var.managed_policy_arns
  role       = aws_iam_role.this.name
  policy_arn = each.value
}

# attach_inline_policy es una bandera estática: count no puede depender de un JSON calculado.
resource "aws_iam_role_policy" "inline" {
  count  = var.attach_inline_policy ? 1 : 0
  name   = "${var.function_name}-inline"
  role   = aws_iam_role.this.id
  policy = var.inline_policy_json
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn
  tags              = var.tags
}

resource "aws_lambda_function" "this" {
  function_name                  = var.function_name
  description                    = var.description
  role                           = aws_iam_role.this.arn
  handler                        = var.handler
  runtime                        = var.runtime
  architectures                  = var.architectures
  memory_size                    = var.memory_size
  timeout                        = var.timeout
  filename                       = data.archive_file.this.output_path
  source_code_hash               = data.archive_file.this.output_base64sha256
  reserved_concurrent_executions = var.reserved_concurrency
  kms_key_arn                    = var.kms_key_arn
  layers                         = var.layers

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.this.name
  }

  tracing_config {
    mode = var.tracing_mode
  }

  dynamic "environment" {
    for_each = length(var.environment) > 0 ? [1] : []
    content {
      variables = var.environment
    }
  }

  dynamic "vpc_config" {
    for_each = length(var.vpc_subnet_ids) > 0 ? [1] : []
    content {
      subnet_ids         = var.vpc_subnet_ids
      security_group_ids = var.vpc_security_group_ids
    }
  }

  dynamic "dead_letter_config" {
    for_each = var.dead_letter_target_arn == null ? [] : [var.dead_letter_target_arn]
    content {
      target_arn = dead_letter_config.value
    }
  }

  tags = var.tags

  depends_on = [
    aws_cloudwatch_log_group.this,
    aws_iam_role_policy_attachment.basic,
    aws_iam_role_policy.inline,
  ]
}
