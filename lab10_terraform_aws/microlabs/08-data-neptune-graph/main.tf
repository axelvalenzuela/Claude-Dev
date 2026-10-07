# Micro lab 08 - Amazon Neptune (base de datos de grafos) con Serverless v2
#   VPC privada sin NAT + Neptune (IAM auth, KMS, audit logs) + Lambda en VPC (openCypher firmado SigV4)
#   + bulk loader desde S3 vía VPC gateway endpoint

data "aws_caller_identity" "current" {}

locals {
  name = "${var.project}-${var.environment}-graph"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
    MicroLab    = "08-data-neptune-graph"
  }
}

module "vpc" {
  source             = "../../modules/vpc"
  name               = local.name
  region             = var.aws_region
  cidr_block         = var.vpc_cidr
  enable_nat_gateway = false # Neptune y Lambda no necesitan Internet; S3 vía gateway endpoint
}

module "kms" {
  source      = "../../modules/kms-key"
  alias       = local.name
  description = "Cifrado de Neptune y datos de carga"
}

module "load_bucket" {
  source      = "../../modules/s3-secure-bucket"
  bucket_name = "${local.name}-load-${data.aws_caller_identity.current.account_id}"
  kms_key_arn = module.kms.key_arn
}

resource "aws_s3_object" "sample" {
  for_each    = fileset("${path.module}/data", "*.csv")
  bucket      = module.load_bucket.bucket_id
  key         = "sample/${each.value}"
  source      = "${path.module}/data/${each.value}"
  source_hash = filemd5("${path.module}/data/${each.value}")
}

# ---------------- Seguridad de red ----------------
resource "aws_security_group" "lambda" {
  name        = "${local.name}-client"
  description = "Clientes de Neptune (Lambda)"
  vpc_id      = module.vpc.vpc_id
}

resource "aws_vpc_security_group_egress_rule" "lambda_to_neptune" {
  security_group_id            = aws_security_group.lambda.id
  referenced_security_group_id = aws_security_group.neptune.id
  ip_protocol                  = "tcp"
  from_port                    = 8182
  to_port                      = 8182
}

resource "aws_vpc_security_group_egress_rule" "lambda_https" {
  security_group_id = aws_security_group.lambda.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  description       = "Gateway endpoints de AWS"
}

resource "aws_security_group" "neptune" {
  name        = "${local.name}-neptune"
  description = "Neptune: solo desde clientes autorizados"
  vpc_id      = module.vpc.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "neptune_from_lambda" {
  security_group_id            = aws_security_group.neptune.id
  referenced_security_group_id = aws_security_group.lambda.id
  ip_protocol                  = "tcp"
  from_port                    = 8182
  to_port                      = 8182
}

# ---------------- Rol del bulk loader ----------------
data "aws_iam_policy_document" "loader_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["rds.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "loader" {
  name               = "${local.name}-s3-loader"
  assume_role_policy = data.aws_iam_policy_document.loader_assume.json
}

resource "aws_iam_role_policy" "loader" {
  name = "read-load-bucket"
  role = aws_iam_role.loader.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:GetObject", "s3:ListBucket"], Resource = [module.load_bucket.bucket_arn, "${module.load_bucket.bucket_arn}/*"] },
      { Effect = "Allow", Action = ["kms:Decrypt"], Resource = module.kms.key_arn },
    ]
  })
}

# ---------------- Neptune ----------------
resource "aws_neptune_subnet_group" "this" {
  name       = local.name
  subnet_ids = module.vpc.data_subnet_ids
}

resource "aws_neptune_cluster_parameter_group" "this" {
  name   = "${local.name}-cluster"
  family = var.neptune_family

  parameter {
    name  = "neptune_enable_audit_log"
    value = "1"
  }

  parameter {
    name  = "neptune_query_timeout"
    value = "20000"
  }
}

resource "aws_neptune_cluster" "this" {
  cluster_identifier                   = local.name
  engine                               = "neptune"
  engine_version                       = var.engine_version
  neptune_subnet_group_name            = aws_neptune_subnet_group.this.name
  vpc_security_group_ids               = [aws_security_group.neptune.id]
  neptune_cluster_parameter_group_name = aws_neptune_cluster_parameter_group.this.name
  iam_database_authentication_enabled  = true
  iam_roles                            = [aws_iam_role.loader.arn]
  storage_encrypted                    = true
  kms_key_arn                          = module.kms.key_arn
  backup_retention_period              = var.backup_retention_days
  preferred_backup_window              = "07:00-08:00"
  enable_cloudwatch_logs_exports       = ["audit"]
  deletion_protection                  = var.deletion_protection
  skip_final_snapshot                  = !var.deletion_protection
  final_snapshot_identifier            = var.deletion_protection ? "${local.name}-final" : null
  apply_immediately                    = true

  serverless_v2_scaling_configuration {
    min_capacity = var.min_ncu
    max_capacity = var.max_ncu
  }
}

resource "aws_neptune_cluster_instance" "this" {
  count                      = var.instance_count
  identifier                 = "${local.name}-${count.index}"
  cluster_identifier         = aws_neptune_cluster.this.id
  engine                     = "neptune"
  instance_class             = "db.serverless"
  neptune_subnet_group_name  = aws_neptune_subnet_group.this.name
  auto_minor_version_upgrade = true
  apply_immediately          = true
}

# ---------------- Cliente Lambda ----------------
data "aws_iam_policy_document" "client" {
  statement {
    sid = "NeptuneDataAccess"
    actions = [
      "neptune-db:connect",
      "neptune-db:ReadDataViaQuery",
      "neptune-db:WriteDataViaQuery",
      "neptune-db:DeleteDataViaQuery",
      "neptune-db:StartLoaderJob",
      "neptune-db:GetLoaderJobStatus",
    ]
    resources = ["arn:aws:neptune-db:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${aws_neptune_cluster.this.cluster_resource_id}/*"]
  }
}

module "client_fn" {
  source                 = "../../modules/lambda-function"
  function_name          = "${local.name}-client"
  description            = "Ejecuta openCypher y cargas masivas en Neptune"
  source_dir             = "${path.module}/src/client"
  timeout                = 30
  vpc_subnet_ids         = module.vpc.app_subnet_ids
  vpc_security_group_ids = [aws_security_group.lambda.id]
  attach_inline_policy   = true
  inline_policy_json     = data.aws_iam_policy_document.client.json
  environment = {
    NEPTUNE_ENDPOINT = aws_neptune_cluster.this.endpoint
    NEPTUNE_PORT     = "8182"
    LOADER_ROLE_ARN  = aws_iam_role.loader.arn
    LOAD_SOURCE      = "s3://${module.load_bucket.bucket_id}/sample/"
  }
}
