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

  hana_sql_ports = [tonumber("3${local.nn}13"), tonumber("3${local.nn}15")]
  hsr_from_port  = tonumber("4${local.nn}01")
  hsr_to_port    = tonumber("4${local.nn}07")

  app_admin_ports = {
    gui   = tonumber("32${local.nn}")
    https = tonumber("443${local.nn}")
  }

  admin_rules = {
    for pair in setproduct(var.admin_cidrs, keys(local.app_admin_ports)) :
    "${pair[0]}-${pair[1]}" => { cidr = pair[0], port = local.app_admin_ports[pair[1]] }
  }
}

# ---------- KMS ----------
resource "aws_kms_key" "sap" {
  description             = "${var.name_prefix} cifrado de EBS y S3 para SAP"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  tags                    = var.tags
}

resource "aws_kms_alias" "sap" {
  name          = "alias/${var.name_prefix}-sap"
  target_key_id = aws_kms_key.sap.key_id
}

# ---------- Security groups ----------
resource "aws_security_group" "hana" {
  name        = "${var.name_prefix}-hana"
  description = "Nodos SAP HANA"
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${var.name_prefix}-hana-sg" })
}

resource "aws_security_group" "app" {
  name        = "${var.name_prefix}-app"
  description = "Servidores de aplicacion ABAP"
  vpc_id      = var.vpc_id
  tags        = merge(var.tags, { Name = "${var.name_prefix}-app-sg" })
}

# App -> HANA (SQL)
resource "aws_vpc_security_group_ingress_rule" "hana_sql_from_app" {
  for_each                     = toset([for p in local.hana_sql_ports : tostring(p)])
  security_group_id            = aws_security_group.hana.id
  referenced_security_group_id = aws_security_group.app.id
  ip_protocol                  = "tcp"
  from_port                    = tonumber(each.value)
  to_port                      = tonumber(each.value)
  description                  = "HANA SQL desde la aplicacion"
}

# HANA <-> HANA (System Replication + SQL entre nodos)
resource "aws_vpc_security_group_ingress_rule" "hana_hsr_self" {
  security_group_id            = aws_security_group.hana.id
  referenced_security_group_id = aws_security_group.hana.id
  ip_protocol                  = "tcp"
  from_port                    = local.hsr_from_port
  to_port                      = local.hsr_to_port
  description                  = "HANA System Replication"
}

resource "aws_vpc_security_group_ingress_rule" "hana_sql_self" {
  security_group_id            = aws_security_group.hana.id
  referenced_security_group_id = aws_security_group.hana.id
  ip_protocol                  = "tcp"
  from_port                    = local.hana_sql_ports[0]
  to_port                      = local.hana_sql_ports[1]
  description                  = "HANA SQL entre nodos"
}

# Trafico interno entre servidores de aplicacion (ASCS/PAS/AAS)
resource "aws_vpc_security_group_ingress_rule" "app_self" {
  security_group_id            = aws_security_group.app.id
  referenced_security_group_id = aws_security_group.app.id
  ip_protocol                  = "-1"
  description                  = "Trafico interno de la aplicacion"
}

# Administradores -> aplicacion (SAP GUI, HTTPS/Fiori)
resource "aws_vpc_security_group_ingress_rule" "app_admin" {
  for_each          = local.admin_rules
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = each.value.cidr
  ip_protocol       = "tcp"
  from_port         = each.value.port
  to_port           = each.value.port
  description       = "Acceso administrativo controlado"
}

resource "aws_vpc_security_group_egress_rule" "hana_all" {
  security_group_id = aws_security_group.hana.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Salida via NAT"
}

resource "aws_vpc_security_group_egress_rule" "app_all" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Salida via NAT"
}

# ---------- IAM (acceso por SSM, sin llaves SSH) ----------
data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sap" {
  name               = "${var.name_prefix}-sap-ec2"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.sap.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

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
    resources = [aws_kms_key.sap.arn]
  }
}

resource "aws_iam_role_policy" "backup" {
  name   = "${var.name_prefix}-backup-access"
  role   = aws_iam_role.sap.id
  policy = data.aws_iam_policy_document.backup.json
}

resource "aws_iam_instance_profile" "sap" {
  name = "${var.name_prefix}-sap-ec2"
  role = aws_iam_role.sap.name
}

output "kms_key_arn" {
  value = aws_kms_key.sap.arn
}

output "hana_sg_id" {
  value = aws_security_group.hana.id
}

output "app_sg_id" {
  value = aws_security_group.app.id
}

output "instance_profile_name" {
  value = aws_iam_instance_profile.sap.name
}
