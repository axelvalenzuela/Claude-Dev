data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "sap" {
  count       = var.ami_id == null ? 1 : 0
  most_recent = true
  owners      = var.ami_owners

  filter {
    name   = "name"
    values = [var.ami_name_pattern]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"
  azs         = slice(data.aws_availability_zones.available.names, 0, 2)
  ami_id      = var.ami_id != null ? var.ami_id : data.aws_ami.sap[0].id

  backup_bucket_name = "${local.name_prefix}-hana-backup-${data.aws_caller_identity.current.account_id}"

  tags = merge({
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Workload    = "sap-s4hana"
  }, var.extra_tags)

  all_hana_nodes = {
    primary   = { subnet_id = module.network.private_subnet_ids[0], az = local.azs[0] }
    secondary = { subnet_id = module.network.private_subnet_ids[1], az = local.azs[1] }
  }

  hana_nodes = { for k, v in local.all_hana_nodes : k => v if k == "primary" || var.ha_enabled }

  app_servers = {
    for i, name in var.app_servers : name => {
      subnet_id = module.network.private_subnet_ids[i % 2]
      az        = local.azs[i % 2]
    }
  }
}

module "network" {
  source = "./modules/network"

  name_prefix          = local.name_prefix
  vpc_cidr             = var.vpc_cidr
  azs                  = local.azs
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidr   = var.public_subnet_cidr
  tags                 = local.tags
}

module "security" {
  source = "./modules/security"

  name_prefix         = local.name_prefix
  vpc_id              = module.network.vpc_id
  vpc_cidr            = var.vpc_cidr
  sap_instance_number = var.sap_instance_number
  admin_cidrs         = var.admin_cidrs
  backup_bucket_name  = local.backup_bucket_name
  tags                = local.tags
}

module "backup_storage" {
  source = "./modules/backup_storage"

  bucket_name    = local.backup_bucket_name
  kms_key_arn    = module.security.kms_key_arn
  retention_days = var.backup_retention_days
  force_destroy  = var.backup_force_destroy
  tags           = local.tags
}

module "hana_nodes" {
  source = "./modules/hana_nodes"

  name_prefix           = local.name_prefix
  nodes                 = local.hana_nodes
  ami_id                = local.ami_id
  instance_type         = var.hana_instance_type
  security_group_ids    = [module.security.hana_sg_id]
  instance_profile_name = module.security.instance_profile_name
  kms_key_arn           = module.security.kms_key_arn
  volumes               = var.hana_volumes

  delete_volumes_on_termination = var.delete_volumes_on_termination
  tags                          = local.tags
}

module "app_server" {
  source = "./modules/app_server"

  name_prefix                   = local.name_prefix
  servers                       = local.app_servers
  ami_id                        = local.ami_id
  instance_type                 = var.app_instance_type
  security_group_ids            = [module.security.app_sg_id]
  instance_profile_name         = module.security.instance_profile_name
  kms_key_arn                   = module.security.kms_key_arn
  delete_volumes_on_termination = var.delete_volumes_on_termination
  tags                          = local.tags
}
