# Micro lab 02 - AWS AppSync (GraphQL) + DynamoDB con resolvers JavaScript (APPSYNC_JS)
# Autorización: Cognito User Pools (usuarios) + AWS_IAM (servicios backend)

locals {
  name = "${var.project}-${var.environment}-gql"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
    MicroLab    = "02-serverless-appsync-graphql"
  }

  resolvers = {
    getNote    = { type = "Query", file = "getNote.js" }
    listNotes  = { type = "Query", file = "listNotes.js" }
    createNote = { type = "Mutation", file = "createNote.js" }
    deleteNote = { type = "Mutation", file = "deleteNote.js" }
  }
}

module "notes_table" {
  source    = "../../modules/dynamodb-table"
  name      = "${local.name}-notes"
  hash_key  = "owner"
  range_key = "id"
}

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
  name                = "${local.name}-client"
  user_pool_id        = aws_cognito_user_pool.this.id
  generate_secret     = false
  explicit_auth_flows = ["ALLOW_USER_PASSWORD_AUTH", "ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
}

# ---------------- Logs ----------------
data "aws_iam_policy_document" "appsync_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["appsync.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "logs" {
  name               = "${local.name}-logs"
  assume_role_policy = data.aws_iam_policy_document.appsync_assume.json
}

resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.logs.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppSyncPushToCloudWatchLogs"
}

# ---------------- API ----------------
resource "aws_appsync_graphql_api" "this" {
  name                 = local.name
  authentication_type  = "AMAZON_COGNITO_USER_POOLS"
  schema               = file("${path.module}/schema.graphql")
  xray_enabled         = true
  query_depth_limit    = var.query_depth_limit
  introspection_config = var.environment == "prod" ? "DISABLED" : "ENABLED"

  user_pool_config {
    aws_region     = var.aws_region
    default_action = "ALLOW"
    user_pool_id   = aws_cognito_user_pool.this.id
  }

  additional_authentication_provider {
    authentication_type = "AWS_IAM"
  }

  log_config {
    cloudwatch_logs_role_arn = aws_iam_role.logs.arn
    field_log_level          = var.field_log_level
    exclude_verbose_content  = true
  }
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/appsync/apis/${aws_appsync_graphql_api.this.id}"
  retention_in_days = var.log_retention_days
}

# ---------------- Data source ----------------
resource "aws_iam_role" "ddb" {
  name               = "${local.name}-ddb-ds"
  assume_role_policy = data.aws_iam_policy_document.appsync_assume.json
}

data "aws_iam_policy_document" "ddb" {
  statement {
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem", "dynamodb:Query"]
    resources = [module.notes_table.table_arn]
  }
}

resource "aws_iam_role_policy" "ddb" {
  name   = "notes-table"
  role   = aws_iam_role.ddb.id
  policy = data.aws_iam_policy_document.ddb.json
}

resource "aws_appsync_datasource" "notes" {
  api_id           = aws_appsync_graphql_api.this.id
  name             = "NotesTable"
  type             = "AMAZON_DYNAMODB"
  service_role_arn = aws_iam_role.ddb.arn

  dynamodb_config {
    table_name = module.notes_table.table_name
    region     = var.aws_region
  }
}

# ---------------- Resolvers JS ----------------
resource "aws_appsync_resolver" "this" {
  for_each    = local.resolvers
  api_id      = aws_appsync_graphql_api.this.id
  type        = each.value.type
  field       = each.key
  kind        = "UNIT"
  data_source = aws_appsync_datasource.notes.name
  code        = file("${path.module}/resolvers/${each.value.file}")

  runtime {
    name            = "APPSYNC_JS"
    runtime_version = "1.0.0"
  }
}

# ---------------- Caché (opcional, con costo por hora) ----------------
resource "aws_appsync_api_cache" "this" {
  count                      = var.enable_cache ? 1 : 0
  api_id                     = aws_appsync_graphql_api.this.id
  api_caching_behavior       = "FULL_REQUEST_CACHING"
  type                       = "SMALL"
  ttl                        = 60
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}

# ---------------- Alarmas ----------------
resource "aws_cloudwatch_metric_alarm" "errors_5xx" {
  alarm_name          = "${local.name}-5xx"
  namespace           = "AWS/AppSync"
  metric_name         = "5XXError"
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 5
  threshold           = 5
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    GraphQLAPIId = aws_appsync_graphql_api.this.id
  }
}
