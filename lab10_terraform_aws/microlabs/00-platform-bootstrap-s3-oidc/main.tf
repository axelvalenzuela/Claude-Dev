# Micro lab 00 - Bootstrap de la plataforma
# 1. Bucket S3 para el estado remoto de Terraform (bloqueo nativo con use_lockfile)
# 2. Proveedor OIDC de GitLab + roles de CI (plan = solo lectura, apply = rama protegida)
# 3. Permissions boundary para el rol de despliegue
# 4. Presupuesto mensual con alertas (pilar de Optimización de Costos)

data "aws_caller_identity" "current" {}

locals {
  name       = "${var.project}-${var.environment}"
  account_id = data.aws_caller_identity.current.account_id

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
    MicroLab    = "00-platform-bootstrap-s3-oidc"
  }
}

# ---------------------------------------------------------------------------
# 1. Estado remoto
# ---------------------------------------------------------------------------
module "state_key" {
  source      = "../../modules/kms-key"
  alias       = "${local.name}-tfstate"
  description = "Cifrado del estado de Terraform"
}

module "state_bucket" {
  source                             = "../../modules/s3-secure-bucket"
  bucket_name                        = "${local.name}-tfstate-${local.account_id}"
  kms_key_arn                        = module.state_key.key_arn
  force_destroy                      = false
  noncurrent_version_expiration_days = 90
}

# ---------------------------------------------------------------------------
# 2. GitLab OIDC (sin llaves de acceso de larga duración)
# ---------------------------------------------------------------------------
resource "aws_iam_openid_connect_provider" "gitlab" {
  url            = "https://${var.gitlab_host}"
  client_id_list = [var.gitlab_audience]
}

data "aws_iam_policy_document" "plan_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.gitlab.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${var.gitlab_host}:aud"
      values   = [var.gitlab_audience]
    }
    # Cualquier rama / MR del proyecto puede hacer plan.
    condition {
      test     = "StringLike"
      variable = "${var.gitlab_host}:sub"
      values   = ["project_path:${var.gitlab_project_path}:ref_type:branch:ref:*"]
    }
  }
}

data "aws_iam_policy_document" "apply_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.gitlab.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${var.gitlab_host}:aud"
      values   = [var.gitlab_audience]
    }
    # Solo la rama por defecto (protegida) puede aplicar cambios.
    condition {
      test     = "StringEquals"
      variable = "${var.gitlab_host}:sub"
      values   = ["project_path:${var.gitlab_project_path}:ref_type:branch:ref:${var.gitlab_default_branch}"]
    }
  }
}

data "aws_iam_policy_document" "state_access" {
  statement {
    sid       = "ListStateBucket"
    actions   = ["s3:ListBucket"]
    resources = [module.state_bucket.bucket_arn]
  }
  statement {
    sid       = "ReadWriteState"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${module.state_bucket.bucket_arn}/*"]
  }
  statement {
    sid       = "UseStateKey"
    actions   = ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"]
    resources = [module.state_key.key_arn]
  }
}

resource "aws_iam_policy" "state_access" {
  name   = "${local.name}-tfstate-access"
  policy = data.aws_iam_policy_document.state_access.json
}

# Permissions boundary: tope máximo de permisos del rol de apply aunque tenga AdministratorAccess.
data "aws_iam_policy_document" "boundary" {
  statement {
    sid       = "AllowAllWithinBoundary"
    actions   = ["*"]
    resources = ["*"]
  }

  statement {
    sid    = "DenyOutsideAllowedRegions"
    effect = "Deny"
    not_actions = [
      "iam:*", "sts:*", "organizations:*", "cloudfront:*", "route53:*", "wafv2:*",
      "support:*", "budgets:*", "ce:*", "health:*", "account:*", "kms:*",
      "s3:GetBucketLocation", "s3:ListAllMyBuckets",
    ]
    resources = ["*"]
    condition {
      test     = "StringNotEquals"
      variable = "aws:RequestedRegion"
      values   = var.allowed_regions
    }
  }

  statement {
    sid    = "DenyGuardrailTampering"
    effect = "Deny"
    actions = [
      "organizations:LeaveOrganization",
      "account:CloseAccount",
      "cloudtrail:StopLogging",
      "cloudtrail:DeleteTrail",
      "guardduty:DeleteDetector",
      "config:StopConfigurationRecorder",
      "config:DeleteConfigurationRecorder",
      "iam:CreateUser",
      "iam:CreateAccessKey",
      "iam:CreateLoginProfile",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "ProtectStateBucket"
    effect    = "Deny"
    actions   = ["s3:DeleteBucket", "s3:PutBucketPolicy", "s3:DeleteBucketPolicy"]
    resources = [module.state_bucket.bucket_arn]
  }

  statement {
    sid       = "ProtectBoundaryItself"
    effect    = "Deny"
    actions   = ["iam:DeletePolicy", "iam:CreatePolicyVersion", "iam:DeleteRolePermissionsBoundary"]
    resources = ["arn:aws:iam::${local.account_id}:policy/${local.name}-ci-boundary"]
  }
}

resource "aws_iam_policy" "boundary" {
  name   = "${local.name}-ci-boundary"
  policy = data.aws_iam_policy_document.boundary.json
}

resource "aws_iam_role" "plan" {
  name                 = "${local.name}-gitlab-plan"
  assume_role_policy   = data.aws_iam_policy_document.plan_trust.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy_attachment" "plan" {
  for_each = {
    readonly = "arn:aws:iam::aws:policy/ReadOnlyAccess"
    state    = aws_iam_policy.state_access.arn
  }
  role       = aws_iam_role.plan.name
  policy_arn = each.value
}

resource "aws_iam_role" "apply" {
  name                 = "${local.name}-gitlab-apply"
  assume_role_policy   = data.aws_iam_policy_document.apply_trust.json
  permissions_boundary = aws_iam_policy.boundary.arn
  max_session_duration = 3600
}

resource "aws_iam_role_policy_attachment" "apply" {
  for_each = {
    admin = "arn:aws:iam::aws:policy/AdministratorAccess"
    state = aws_iam_policy.state_access.arn
  }
  role       = aws_iam_role.apply.name
  policy_arn = each.value
}

# ---------------------------------------------------------------------------
# 4. Presupuesto y alertas de costo
# ---------------------------------------------------------------------------
resource "aws_budgets_budget" "monthly" {
  name         = "${local.name}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = length(var.alert_emails) > 0 ? [50, 80, 100] : []
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = notification.value == 100 ? "FORECASTED" : "ACTUAL"
      subscriber_email_addresses = var.alert_emails
    }
  }
}
