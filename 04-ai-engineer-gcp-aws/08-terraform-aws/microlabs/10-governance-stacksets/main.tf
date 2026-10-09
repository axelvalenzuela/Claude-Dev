# Micro lab 10 - AWS CloudFormation StackSets: baseline de seguridad multi-cuenta / multi-región
#   Cuenta administradora (management o delegated admin) -> StackSet SERVICE_MANAGED -> OUs destino
#   + bus de eventos central que recibe hallazgos y actividad root de todas las cuentas

data "aws_caller_identity" "current" {}

locals {
  name = "${var.project}-${var.environment}-stacksets"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
    MicroLab    = "10-governance-stacksets"
  }

  audit_account_id = coalesce(var.audit_account_id, data.aws_caller_identity.current.account_id)
}

# ---------------- Hub: bus central de eventos de seguridad ----------------
resource "aws_cloudwatch_event_bus" "security" {
  name = "${local.name}-security-central"
}

data "aws_iam_policy_document" "security_bus" {
  statement {
    sid       = "AllowOrganizationAccounts"
    actions   = ["events:PutEvents"]
    resources = [aws_cloudwatch_event_bus.security.arn]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:PrincipalOrgID"
      values   = [var.organization_id]
    }
  }
}

resource "aws_cloudwatch_event_bus_policy" "security" {
  event_bus_name = aws_cloudwatch_event_bus.security.name
  policy         = data.aws_iam_policy_document.security_bus.json
}

module "alerts" {
  source              = "../../modules/sns-alerts"
  name                = "${local.name}-security-alerts"
  email_subscriptions = var.security_emails
}

resource "aws_cloudwatch_event_rule" "all_security" {
  name           = "${local.name}-to-sns"
  event_bus_name = aws_cloudwatch_event_bus.security.name
  event_pattern  = jsonencode({ account = [{ exists = true }] })
}

resource "aws_cloudwatch_event_target" "sns" {
  rule           = aws_cloudwatch_event_rule.all_security.name
  event_bus_name = aws_cloudwatch_event_bus.security.name
  arn            = module.alerts.topic_arn

  input_transformer {
    input_paths = {
      account = "$.account"
      region  = "$.region"
      type    = "$.detail-type"
      source  = "$.source"
    }
    input_template = "\"[08-terraform-aws security] <type> (<source>) en la cuenta <account> / <region>\""
  }
}

# ---------------- Rol de administración (solo SELF_MANAGED) ----------------
data "aws_iam_policy_document" "admin_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["cloudformation.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "stackset_admin" {
  count              = var.permission_model == "SELF_MANAGED" ? 1 : 0
  name               = "AWSCloudFormationStackSetAdministrationRole"
  assume_role_policy = data.aws_iam_policy_document.admin_assume.json
}

resource "aws_iam_role_policy" "stackset_admin" {
  count = var.permission_model == "SELF_MANAGED" ? 1 : 0
  name  = "assume-execution-role"
  role  = aws_iam_role.stackset_admin[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sts:AssumeRole"
      Resource = "arn:aws:iam::*:role/AWSCloudFormationStackSetExecutionRole"
    }]
  })
}

# ---------------- StackSet ----------------
resource "aws_cloudformation_stack_set" "baseline" {
  name             = "${local.name}-security-baseline"
  description      = "Baseline de seguridad 08-terraform-aws (versión ${var.baseline_version})"
  permission_model = var.permission_model
  call_as          = var.call_as
  capabilities     = ["CAPABILITY_NAMED_IAM"]
  template_body    = file("${path.module}/templates/security-baseline.yaml")

  administration_role_arn = var.permission_model == "SELF_MANAGED" ? aws_iam_role.stackset_admin[0].arn : null
  execution_role_name     = var.permission_model == "SELF_MANAGED" ? "AWSCloudFormationStackSetExecutionRole" : null

  parameters = {
    AuditAccountId     = local.audit_account_id
    CentralEventBusArn = aws_cloudwatch_event_bus.security.arn
    EnableConfigRules  = tostring(var.enable_config_rules)
    BaselineVersion    = var.baseline_version
  }

  dynamic "auto_deployment" {
    for_each = var.permission_model == "SERVICE_MANAGED" ? [1] : []
    content {
      enabled                          = true # cuentas nuevas en la OU reciben el baseline automáticamente
      retain_stacks_on_account_removal = false
    }
  }

  managed_execution {
    active = true # serializa operaciones en conflicto en lugar de fallar
  }

  operation_preferences {
    region_concurrency_type      = "PARALLEL"
    max_concurrent_percentage    = var.max_concurrent_percentage
    failure_tolerance_percentage = var.failure_tolerance_percentage
  }

  lifecycle {
    # AWS lo gestiona en SERVICE_MANAGED y genera drift perpetuo.
    ignore_changes = [administration_role_arn]
  }
}

# Una instancia por región; dentro de cada región se despliega a todas las cuentas de las OUs.
resource "aws_cloudformation_stack_set_instance" "ous" {
  for_each                  = var.permission_model == "SERVICE_MANAGED" ? toset(var.target_regions) : toset([])
  stack_set_name            = aws_cloudformation_stack_set.baseline.name
  call_as                   = var.call_as
  stack_set_instance_region = each.value

  deployment_targets {
    organizational_unit_ids = var.target_ou_ids
  }

  operation_preferences {
    region_concurrency_type      = "PARALLEL"
    max_concurrent_percentage    = var.max_concurrent_percentage
    failure_tolerance_percentage = var.failure_tolerance_percentage
  }
}

# SELF_MANAGED: cuentas explícitas x regiones.
resource "aws_cloudformation_stack_set_instance" "accounts" {
  for_each = var.permission_model == "SELF_MANAGED" ? {
    for pair in setproduct(var.target_account_ids, var.target_regions) : "${pair[0]}-${pair[1]}" => {
      account = pair[0]
      region  = pair[1]
    }
  } : {}

  stack_set_name            = aws_cloudformation_stack_set.baseline.name
  account_id                = each.value.account
  stack_set_instance_region = each.value.region
}
