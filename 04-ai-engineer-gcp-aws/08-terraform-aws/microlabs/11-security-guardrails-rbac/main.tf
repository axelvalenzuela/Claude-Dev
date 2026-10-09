# Micro lab 11 - Seguridad y gobernanza de cuenta
#   Detectivos: CloudTrail, AWS Config, GuardDuty, Security Hub (FSBP + CIS), IAM Access Analyzer
#   Preventivos: password policy, S3 Block Public Access de cuenta, cifrado EBS por defecto, SCPs (opcional)
#   Identidad: roles RBAC con MFA + permissions boundary + ejemplo ABAC por etiquetas

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

locals {
  name              = "${var.project}-${var.environment}-sec"
  account_id        = data.aws_caller_identity.current.account_id
  trail_bucket_name = "${local.name}-audit-${local.account_id}"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
    MicroLab    = "11-security-guardrails-rbac"
  }
}

module "kms" {
  source             = "../../modules/kms-key"
  alias              = "${local.name}-audit"
  description        = "Cifrado de CloudTrail, Config y alertas de seguridad"
  service_principals = ["cloudtrail.amazonaws.com", "config.amazonaws.com", "events.amazonaws.com", "sns.amazonaws.com"]
}

# ===========================================================================
# Bucket de auditoría (CloudTrail + Config)
# ===========================================================================
data "aws_iam_policy_document" "audit_bucket" {
  statement {
    sid       = "AclCheck"
    actions   = ["s3:GetBucketAcl"]
    resources = ["arn:aws:s3:::${local.trail_bucket_name}"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com", "config.amazonaws.com"]
    }
  }
  statement {
    sid       = "CloudTrailWrite"
    actions   = ["s3:PutObject"]
    resources = ["arn:aws:s3:::${local.trail_bucket_name}/cloudtrail/AWSLogs/${local.account_id}/*"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = ["arn:${data.aws_partition.current.partition}:cloudtrail:${var.aws_region}:${local.account_id}:trail/${local.name}-trail"]
    }
  }
  statement {
    sid       = "ConfigWrite"
    actions   = ["s3:PutObject"]
    resources = ["arn:aws:s3:::${local.trail_bucket_name}/config/AWSLogs/${local.account_id}/*"]
    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }
  }
  statement {
    sid       = "ConfigListBucket"
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::${local.trail_bucket_name}"]
    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }
  }
}

module "audit_bucket" {
  source                             = "../../modules/s3-secure-bucket"
  bucket_name                        = local.trail_bucket_name
  kms_key_arn                        = module.kms.key_arn
  force_destroy                      = var.environment != "prod"
  transition_to_ia_days              = 30
  expiration_days                    = var.audit_log_retention_days
  noncurrent_version_expiration_days = 30
  additional_policy_json             = data.aws_iam_policy_document.audit_bucket.json
}

# ===========================================================================
# CloudTrail
# ===========================================================================
resource "aws_cloudtrail" "this" {
  name                          = "${local.name}-trail"
  s3_bucket_name                = module.audit_bucket.bucket_id
  s3_key_prefix                 = "cloudtrail"
  is_multi_region_trail         = true
  include_global_service_events = true
  enable_log_file_validation    = true # detecta manipulación de logs
  kms_key_id                    = module.kms.key_arn
}

# ===========================================================================
# AWS Config
# ===========================================================================
data "aws_iam_policy_document" "config_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "config" {
  name               = "${local.name}-config"
  assume_role_policy = data.aws_iam_policy_document.config_assume.json
}

resource "aws_iam_role_policy_attachment" "config" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
}

resource "aws_iam_role_policy" "config_kms" {
  name = "kms-audit-key"
  role = aws_iam_role.config.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["kms:GenerateDataKey", "kms:Decrypt"], Resource = module.kms.key_arn }]
  })
}

resource "aws_config_configuration_recorder" "this" {
  name     = "default"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = var.record_global_resources
  }

  recording_mode {
    recording_frequency = var.config_recording_frequency
  }
}

resource "aws_config_delivery_channel" "this" {
  name           = "default"
  s3_bucket_name = module.audit_bucket.bucket_id
  s3_key_prefix  = "config"
  s3_kms_key_arn = module.kms.key_arn

  snapshot_delivery_properties {
    delivery_frequency = "TwentyFour_Hours"
  }

  depends_on = [aws_config_configuration_recorder.this]
}

resource "aws_config_configuration_recorder_status" "this" {
  name       = aws_config_configuration_recorder.this.name
  is_enabled = true
  depends_on = [aws_config_delivery_channel.this]
}

resource "aws_config_config_rule" "managed" {
  for_each = var.config_managed_rules
  name     = "${local.name}-${lower(replace(each.key, "_", "-"))}"

  source {
    owner             = "AWS"
    source_identifier = each.key
  }

  input_parameters = each.value == "" ? null : each.value
  depends_on       = [aws_config_configuration_recorder_status.this]
}

# ===========================================================================
# GuardDuty + Security Hub + Access Analyzer
# ===========================================================================
resource "aws_guardduty_detector" "this" {
  enable                       = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"
}

resource "aws_guardduty_detector_feature" "this" {
  for_each    = toset(var.guardduty_features)
  detector_id = aws_guardduty_detector.this.id
  name        = each.value
  status      = "ENABLED"
}

resource "aws_securityhub_account" "this" {
  enable_default_standards  = false
  control_finding_generator = "SECURITY_CONTROL"
  auto_enable_controls      = true
}

resource "aws_securityhub_standards_subscription" "this" {
  for_each      = toset(var.securityhub_standards)
  standards_arn = "arn:${data.aws_partition.current.partition}:securityhub:${var.aws_region}::standards/${each.value}"
  depends_on    = [aws_securityhub_account.this]
}

resource "aws_accessanalyzer_analyzer" "this" {
  analyzer_name = "${local.name}-account"
  type          = "ACCOUNT"
}

# Alertas: hallazgos altos de GuardDuty / Security Hub -> SNS
module "alerts" {
  source              = "../../modules/sns-alerts"
  name                = "${local.name}-findings"
  kms_key_arn         = module.kms.key_arn
  email_subscriptions = var.security_emails
}

resource "aws_cloudwatch_event_rule" "findings" {
  name = "${local.name}-high-findings"
  event_pattern = jsonencode({
    source = ["aws.guardduty", "aws.securityhub"]
    "$or" = [
      { detail = { severity = [{ numeric = [">=", 7] }] } },
      { detail = { findings = { Severity = { Label = ["CRITICAL", "HIGH"] } } } },
    ]
  })
}

resource "aws_cloudwatch_event_target" "findings" {
  rule = aws_cloudwatch_event_rule.findings.name
  arn  = module.alerts.topic_arn
}

# ===========================================================================
# Controles preventivos a nivel de cuenta
# ===========================================================================
resource "aws_iam_account_password_policy" "this" {
  minimum_password_length        = 14
  require_lowercase_characters   = true
  require_uppercase_characters   = true
  require_numbers                = true
  require_symbols                = true
  allow_users_to_change_password = true
  password_reuse_prevention      = 24
  max_password_age               = 90
}

resource "aws_s3_account_public_access_block" "this" {
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_ebs_encryption_by_default" "this" {
  enabled = true
}

# ===========================================================================
# RBAC: roles por función, asumibles solo con MFA, con permissions boundary
# (En producción, prefiere IAM Identity Center con permission sets equivalentes.)
# ===========================================================================
resource "aws_iam_policy" "developer_boundary" {
  name   = "${local.name}-developer-boundary"
  policy = file("${path.module}/policies/developer-boundary.json")
}

resource "aws_iam_policy" "abac_ec2" {
  name   = "${local.name}-abac-ec2-by-team"
  policy = file("${path.module}/policies/abac-ec2-team.json")
}

data "aws_iam_policy_document" "rbac_trust" {
  for_each = var.rbac_roles
  statement {
    actions = ["sts:AssumeRole", "sts:TagSession"]
    principals {
      type        = "AWS"
      identifiers = length(each.value.trusted_principals) > 0 ? each.value.trusted_principals : ["arn:${data.aws_partition.current.partition}:iam::${local.account_id}:root"]
    }
    condition {
      test     = "Bool"
      variable = "aws:MultiFactorAuthPresent"
      values   = ["true"]
    }
    condition {
      test     = "NumericLessThan"
      variable = "aws:MultiFactorAuthAge"
      values   = ["3600"]
    }
  }
}

resource "aws_iam_role" "rbac" {
  for_each             = var.rbac_roles
  name                 = "${local.name}-${each.key}"
  description          = each.value.description
  assume_role_policy   = data.aws_iam_policy_document.rbac_trust[each.key].json
  max_session_duration = each.value.max_session_hours * 3600
  permissions_boundary = each.value.use_boundary ? aws_iam_policy.developer_boundary.arn : null
}

locals {
  rbac_attachments = merge([
    for role, cfg in var.rbac_roles : {
      for idx, arn in cfg.managed_policy_arns : "${role}-${idx}" => { role = role, arn = arn }
    }
  ]...)
}

resource "aws_iam_role_policy_attachment" "rbac" {
  for_each   = local.rbac_attachments
  role       = aws_iam_role.rbac[each.value.role].name
  policy_arn = each.value.arn
}

resource "aws_iam_role_policy_attachment" "developer_abac" {
  count      = contains(keys(var.rbac_roles), "developer") ? 1 : 0
  role       = aws_iam_role.rbac["developer"].name
  policy_arn = aws_iam_policy.abac_ec2.arn
}

# Alerta cada vez que alguien asume el rol break-glass.
resource "aws_cloudwatch_event_rule" "break_glass" {
  count = contains(keys(var.rbac_roles), "break-glass-admin") ? 1 : 0
  name  = "${local.name}-break-glass-used"
  event_pattern = jsonencode({
    source        = ["aws.sts"]
    "detail-type" = ["AWS API Call via CloudTrail"]
    detail = {
      eventName         = ["AssumeRole"]
      requestParameters = { roleArn = [aws_iam_role.rbac["break-glass-admin"].arn] }
    }
  })
}

resource "aws_cloudwatch_event_target" "break_glass" {
  count = contains(keys(var.rbac_roles), "break-glass-admin") ? 1 : 0
  rule  = aws_cloudwatch_event_rule.break_glass[0].name
  arn   = module.alerts.topic_arn
}

# ===========================================================================
# SCPs (solo si esta cuenta es management de AWS Organizations)
# ===========================================================================
resource "aws_organizations_policy" "scp" {
  for_each    = var.manage_scps ? fileset("${path.module}/policies/scp", "*.json") : toset([])
  name        = "aie-${trimsuffix(each.value, ".json")}"
  description = "SCP 08-terraform-aws: ${trimsuffix(each.value, ".json")}"
  type        = "SERVICE_CONTROL_POLICY"
  content     = file("${path.module}/policies/scp/${each.value}")
}

resource "aws_organizations_policy_attachment" "scp" {
  for_each = var.manage_scps ? {
    for pair in setproduct(tolist(fileset("${path.module}/policies/scp", "*.json")), var.scp_target_ids) : "${pair[0]}|${pair[1]}" => {
      policy = pair[0]
      target = pair[1]
    }
  } : {}
  policy_id = aws_organizations_policy.scp[each.value.policy].id
  target_id = each.value.target
}
