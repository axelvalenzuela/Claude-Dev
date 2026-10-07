# Micro lab 04 - Chatbot de IA generativa: HTTP API + Lambda + Amazon Bedrock (Converse API)
#   + Bedrock Guardrails (filtros de contenido, PII, temas prohibidos)
#   + DynamoDB para historial de conversación con TTL

data "aws_caller_identity" "current" {}

locals {
  name = "${var.project}-${var.environment}-chat"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
    MicroLab    = "04-chatbot-bedrock"
  }
}

# ---------------- Historial ----------------
module "history" {
  source         = "../../modules/dynamodb-table"
  name           = "${local.name}-history"
  hash_key       = "session_id"
  range_key      = "ts"
  range_key_type = "N"
  ttl_attribute  = "expires_at"
}

# ---------------- Guardrail ----------------
resource "aws_bedrock_guardrail" "this" {
  name                      = "${local.name}-guardrail"
  description               = "Guardrail del chatbot del lab10"
  blocked_input_messaging   = "Lo siento, no puedo procesar esa solicitud."
  blocked_outputs_messaging = "Lo siento, no puedo responder eso."

  content_policy_config {
    dynamic "filters_config" {
      for_each = ["HATE", "INSULTS", "SEXUAL", "VIOLENCE", "MISCONDUCT"]
      content {
        type            = filters_config.value
        input_strength  = "HIGH"
        output_strength = "HIGH"
      }
    }
    filters_config {
      type            = "PROMPT_ATTACK"
      input_strength  = "HIGH"
      output_strength = "NONE"
    }
  }

  sensitive_information_policy_config {
    dynamic "pii_entities_config" {
      for_each = ["EMAIL", "PHONE", "CREDIT_DEBIT_CARD_NUMBER", "AWS_ACCESS_KEY", "AWS_SECRET_KEY"]
      content {
        type   = pii_entities_config.value
        action = pii_entities_config.value == "EMAIL" || pii_entities_config.value == "PHONE" ? "ANONYMIZE" : "BLOCK"
      }
    }
  }

  topic_policy_config {
    topics_config {
      name       = "asesoria-financiera"
      type       = "DENY"
      definition = "Recomendaciones de inversión, compra o venta de acciones, criptomonedas o productos financieros."
      examples   = ["¿En qué acciones debo invertir?", "¿Compro bitcoin hoy?"]
    }
  }

  word_policy_config {
    managed_word_lists_config {
      type = "PROFANITY"
    }
  }
}

resource "aws_bedrock_guardrail_version" "this" {
  guardrail_arn = aws_bedrock_guardrail.this.guardrail_arn
  description   = "Versión publicada por Terraform"
}

# ---------------- Lambda ----------------
data "aws_iam_policy_document" "chat" {
  statement {
    sid     = "InvokeModel"
    actions = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = [
      "arn:aws:bedrock:*::foundation-model/*",
      "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/*",
    ]
  }
  statement {
    sid       = "ApplyGuardrail"
    actions   = ["bedrock:ApplyGuardrail"]
    resources = [aws_bedrock_guardrail.this.guardrail_arn]
  }
  statement {
    sid       = "History"
    actions   = ["dynamodb:PutItem", "dynamodb:Query", "dynamodb:BatchWriteItem"]
    resources = [module.history.table_arn]
  }
}

module "chat_fn" {
  source               = "../../modules/lambda-function"
  function_name        = "${local.name}-handler"
  description          = "Orquesta la conversación con Bedrock"
  source_dir           = "${path.module}/src/chat"
  memory_size          = 512
  timeout              = 60
  reserved_concurrency = var.max_concurrency
  attach_inline_policy = true
  inline_policy_json   = data.aws_iam_policy_document.chat.json
  environment = {
    MODEL_ID          = var.model_id
    GUARDRAIL_ID      = aws_bedrock_guardrail.this.guardrail_id
    GUARDRAIL_VERSION = aws_bedrock_guardrail_version.this.version
    TABLE_NAME        = module.history.table_name
    HISTORY_TURNS     = tostring(var.history_turns)
    MAX_TOKENS        = tostring(var.max_tokens)
    SYSTEM_PROMPT     = var.system_prompt
    TTL_HOURS         = "24"
  }
}

# ---------------- Identidad ----------------
resource "aws_cognito_user_pool" "this" {
  name                     = "${local.name}-users"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }
}

resource "aws_cognito_user_pool_client" "this" {
  name                = "${local.name}-web"
  user_pool_id        = aws_cognito_user_pool.this.id
  generate_secret     = false
  explicit_auth_flows = ["ALLOW_USER_PASSWORD_AUTH", "ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
}

# ---------------- HTTP API ----------------
resource "aws_apigatewayv2_api" "this" {
  name          = local.name
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.allowed_origins
    allow_methods = ["POST", "OPTIONS"]
    allow_headers = ["authorization", "content-type"]
    max_age       = 3600
  }
}

resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.this.id
  name             = "cognito"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.this.id}"
    audience = [aws_cognito_user_pool_client.this.id]
  }
}

resource "aws_apigatewayv2_integration" "chat" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = module.chat_fn.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 30000
}

resource "aws_apigatewayv2_route" "chat" {
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = "POST /chat"
  target             = "integrations/${aws_apigatewayv2_integration.chat.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_cloudwatch_log_group" "access" {
  name              = "/apigw/${local.name}/access"
  retention_in_days = 30
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit  = var.throttle_rate_limit
    throttling_burst_limit = var.throttle_rate_limit * 2
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.access.arn
    format = jsonencode({
      requestId = "$context.requestId"
      user      = "$context.authorizer.claims.sub"
      route     = "$context.routeKey"
      status    = "$context.status"
      latency   = "$context.integrationLatency"
      error     = "$context.integrationErrorMessage"
    })
  }
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowHttpApiInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.chat_fn.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*/chat"
}

# ---------------- Observabilidad de costo/uso de IA ----------------
resource "aws_cloudwatch_metric_alarm" "throttles" {
  alarm_name          = "${local.name}-bedrock-throttles"
  namespace           = "AWS/Bedrock"
  metric_name         = "InvocationThrottles"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    ModelId = var.model_id
  }
}

resource "aws_cloudwatch_metric_alarm" "output_tokens" {
  alarm_name          = "${local.name}-output-tokens-hourly"
  alarm_description   = "Consumo de tokens por encima de lo esperado (control de costos)"
  namespace           = "AWS/Bedrock"
  metric_name         = "OutputTokenCount"
  statistic           = "Sum"
  period              = 3600
  evaluation_periods  = 1
  threshold           = var.hourly_output_token_alarm
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    ModelId = var.model_id
  }
}
