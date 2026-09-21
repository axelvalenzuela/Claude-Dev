variable "name_prefix" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "sap_instance_number" {
  type        = string
  description = "Numero de instancia SAP (NN) de dos digitos; define los puertos."
}

variable "admin_cidrs" {
  type        = list(string)
  default     = []
  description = "CIDRs autorizados a SAP GUI y HTTPS. Vacio = ningun acceso externo a la app."
}

variable "backup_bucket_name" {
  type        = string
  description = "Nombre del bucket de backup (para la politica IAM)."
}

variable "tags" {
  type    = map(string)
  default = {}
}

locals {
  nn = var.sap_instance_number

  hana_sql_from = tonumber("3${local.nn}13")
  hana_sql_to   = tonumber("3${local.nn}15")
  hsr_from      = tonumber("4${local.nn}01")
  hsr_to        = tonumber("4${local.nn}07")

  app_admin_ports = {
    gui   = tonumber("32${local.nn}")
    https = tonumber("443${local.nn}")
  }

  admin_rules = [
    for pair in setproduct(var.admin_cidrs, keys(local.app_admin_ports)) : {
      from_port   = local.app_admin_ports[pair[1]]
      to_port     = local.app_admin_ports[pair[1]]
      protocol    = "tcp"
      cidr_blocks = pair[0]
      description = "Acceso administrativo controlado (${pair[1]})"
    }
  ]
}

# ---------- KMS ----------
module "kms" {
  source  = "terraform-aws-modules/kms/aws"
  version = "~> 3.0"

  description             = "${var.name_prefix} cifrado de EBS y S3 para SAP"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  enable_default_policy   = true
  aliases                 = ["${var.name_prefix}-sap"]

  tags = var.tags
}

# ---------- Security groups ----------
module "app_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "${var.name_prefix}-app"
  description = "Servidores de aplicacion ABAP"
  vpc_id      = var.vpc_id

  ingress_with_self = [
    { rule = "all-all", description = "Trafico interno de la aplicacion" }
  ]
  ingress_with_cidr_blocks = local.admin_rules
  egress_rules             = ["all-all"]

  tags = var.tags
}

module "hana_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "${var.name_prefix}-hana"
  description = "Nodos SAP HANA"
  vpc_id      = var.vpc_id

  # Aplicacion -> HANA (SQL). El ID del SG de la app se conoce hasta el apply.
  computed_ingress_with_source_security_group_id = [
    {
      from_port                = local.hana_sql_from
      to_port                  = local.hana_sql_to
      protocol                 = "tcp"
      description              = "HANA SQL desde la aplicacion"
      source_security_group_id = module.app_sg.security_group_id
    }
  ]
  number_of_computed_ingress_with_source_security_group_id = 1

  # HANA <-> HANA: System Replication y SQL entre nodos
  ingress_with_self = [
    {
      from_port   = local.hsr_from
      to_port     = local.hsr_to
      protocol    = "tcp"
      description = "HANA System Replication"
    },
    {
      from_port   = local.hana_sql_from
      to_port     = local.hana_sql_to
      protocol    = "tcp"
      description = "HANA SQL entre nodos"
    }
  ]
  egress_rules = ["all-all"]

  tags = var.tags
}

# ---------- IAM (acceso por SSM, sin llaves SSH) ----------
data "aws_iam_policy_document" "backup" {
  statement {
    sid       = "BackupBucketList"
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = ["arn:aws:s3:::${var.backup_bucket_name}"]
  }
  statement {
    sid       = "BackupObjects"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload"]
    resources = ["arn:aws:s3:::${var.backup_bucket_name}/*"]
  }
  statement {
    sid       = "BackupKms"
    actions   = ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"]
    resources = [module.kms.key_arn]
  }
}

module "backup_policy" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-policy"
  version = "~> 5.0"

  name   = "${var.name_prefix}-backup-access"
  policy = data.aws_iam_policy_document.backup.json

  tags = var.tags
}

module "sap_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-assumable-role"
  version = "~> 5.0"

  create_role             = true
  role_name               = "${var.name_prefix}-sap-ec2"
  create_instance_profile = true
  role_requires_mfa       = false
  trusted_role_services   = ["ec2.amazonaws.com"]

  custom_role_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    module.backup_policy.arn,
  ]
  number_of_custom_role_policy_arns = 2

  tags = var.tags
}

output "kms_key_arn" {
  value = module.kms.key_arn
}

output "hana_sg_id" {
  value = module.hana_sg.security_group_id
}

output "app_sg_id" {
  value = module.app_sg.security_group_id
}

output "instance_profile_name" {
  value = module.sap_role.iam_instance_profile_name
}
