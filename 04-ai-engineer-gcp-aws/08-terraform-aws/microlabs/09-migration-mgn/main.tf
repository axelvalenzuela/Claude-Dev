# Micro lab 09 - Migración rehost (lift & shift) con AWS Application Migration Service (MGN)
# Terraform crea la "landing zone" de la migración; la configuración de MGN se aplica con
# scripts/configure-mgn.sh (AWS CLI) usando los templates de templates/*.json.

data "aws_caller_identity" "current" {}

locals {
  name = "${var.project}-${var.environment}-mgn"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
    MicroLab    = "09-migration-mgn"
  }
}

# ---------------- Red: staging (replicación) + target (cutover) ----------------
module "vpc" {
  source             = "../../modules/vpc"
  name               = local.name
  region             = var.aws_region
  cidr_block         = var.vpc_cidr
  enable_nat_gateway = var.enable_nat_gateway
}

# Subnet de staging dedicada: aloja los replication servers ligeros de MGN.
resource "aws_subnet" "staging" {
  vpc_id                  = module.vpc.vpc_id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 30)
  availability_zone       = module.vpc.azs[0]
  map_public_ip_on_launch = false
  tags                    = { Name = "${local.name}-staging", Tier = "mgn-staging" }
}

resource "aws_route_table_association" "staging" {
  subnet_id      = aws_subnet.staging.id
  route_table_id = var.replication_over_private_link ? module.vpc.app_route_table_ids[0] : aws_route_table.staging_public[0].id
}

resource "aws_route_table" "staging_public" {
  count  = var.replication_over_private_link ? 0 : 1
  vpc_id = module.vpc.vpc_id
  tags   = { Name = "${local.name}-staging-public-rt" }
}

resource "aws_route" "staging_internet" {
  count                  = var.replication_over_private_link ? 0 : 1
  route_table_id         = aws_route_table.staging_public[0].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = module.vpc.internet_gateway_id
}

# Replication servers: reciben datos de los agentes en TCP 1500 y hablan con MGN/S3/EC2 por 443.
resource "aws_security_group" "replication" {
  name        = "${local.name}-replication"
  description = "MGN replication servers"
  vpc_id      = module.vpc.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "replication_1500" {
  for_each          = toset(var.source_cidrs)
  security_group_id = aws_security_group.replication.id
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 1500
  to_port           = 1500
  description       = "Replicación de bloques desde el datacenter origen"
}

resource "aws_vpc_security_group_egress_rule" "replication_443" {
  security_group_id = aws_security_group.replication.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

# Servidores migrados (test y cutover)
resource "aws_security_group" "target" {
  name        = "${local.name}-target"
  description = "Servidores migrados: ajusta según la aplicación"
  vpc_id      = module.vpc.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "target_app" {
  for_each          = toset([for p in var.target_app_ports : tostring(p)])
  security_group_id = aws_security_group.target.id
  cidr_ipv4         = var.vpc_cidr
  ip_protocol       = "tcp"
  from_port         = tonumber(each.value)
  to_port           = tonumber(each.value)
}

resource "aws_vpc_security_group_egress_rule" "target_all" {
  security_group_id = aws_security_group.target.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# ---------------- Cifrado de discos replicados ----------------
module "kms" {
  source      = "../../modules/kms-key"
  alias       = local.name
  description = "Cifrado de volúmenes EBS de staging y servidores migrados"
}

# ---------------- Identidades ----------------
# Rol que el operador asume para obtener credenciales TEMPORALES al instalar el agente
# (evita crear usuarios IAM con llaves de larga duración).
data "aws_iam_policy_document" "installer_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = length(var.installer_principal_arns) > 0 ? var.installer_principal_arns : ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    condition {
      test     = "Bool"
      variable = "aws:MultiFactorAuthPresent"
      values   = ["true"]
    }
  }
}

resource "aws_iam_role" "agent_installer" {
  name                 = "${local.name}-agent-installer"
  assume_role_policy   = data.aws_iam_policy_document.installer_assume.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy_attachment" "agent_installer" {
  role       = aws_iam_role.agent_installer.name
  policy_arn = "arn:aws:iam::aws:policy/AWSApplicationMigrationAgentInstallationPolicy"
}

# Perfil para servidores migrados: SSM (sin SSH) + CloudWatch Agent
data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "target" {
  name               = "${local.name}-target-instance"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

resource "aws_iam_role_policy_attachment" "target" {
  for_each = {
    ssm = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    cw  = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  }
  role       = aws_iam_role.target.name
  policy_arn = each.value
}

resource "aws_iam_instance_profile" "target" {
  name = "${local.name}-target"
  role = aws_iam_role.target.name
}

# ---------------- Plantillas renderizadas para el script de MGN ----------------
resource "local_file" "replication_template" {
  filename = "${path.module}/.build/replication-template.json"
  content = templatefile("${path.module}/templates/replication-template.json.tpl", {
    staging_subnet_id    = aws_subnet.staging.id
    replication_sg_id    = aws_security_group.replication.id
    kms_key_arn          = module.kms.key_arn
    use_private_ip       = var.replication_over_private_link
    bandwidth_throttle   = var.bandwidth_throttle_mbps
    replication_instance = var.replication_server_instance_type
    project              = var.project
  })
}

resource "local_file" "launch_overrides" {
  filename = "${path.module}/.build/launch-template-overrides.json"
  content = templatefile("${path.module}/templates/launch-template-overrides.json.tpl", {
    target_subnet_id     = module.vpc.app_subnet_ids[0]
    target_sg_id         = aws_security_group.target.id
    instance_profile_arn = aws_iam_instance_profile.target.arn
    kms_key_arn          = module.kms.key_arn
    project              = var.project
  })
}
