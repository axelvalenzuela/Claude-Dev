# Micro lab 06 - Arquitectura web de 3 niveles (clásica, IaaS/PaaS)
#   VPC (módulo compartido) + web-tier (ALB+WAF) + app-tier (ASG) + data-tier (RDS Multi-AZ)
#   Cadena de security groups: Internet -> ALB -> App -> DB  (cada capa solo habla con la siguiente)

locals {
  name = "${var.project}-${var.environment}-3t"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    CostCenter  = var.cost_center
    ManagedBy   = "Terraform"
    MicroLab    = "06-three-tier-web"
  }
}

module "vpc" {
  source             = "../../modules/vpc"
  name               = local.name
  region             = var.aws_region
  cidr_block         = var.vpc_cidr
  az_count           = var.az_count
  enable_nat_gateway = true
  single_nat_gateway = var.single_nat_gateway
}

module "data" {
  source               = "./modules/data-tier"
  name                 = local.name
  vpc_id               = module.vpc.vpc_id
  data_subnet_ids      = module.vpc.data_subnet_ids
  instance_class       = var.db_instance_class
  allocated_storage_gb = var.db_allocated_storage_gb
  multi_az             = var.db_multi_az
  deletion_protection  = var.deletion_protection
}

module "web" {
  source              = "./modules/web-tier"
  name                = local.name
  vpc_id              = module.vpc.vpc_id
  vpc_cidr            = module.vpc.vpc_cidr
  public_subnet_ids   = module.vpc.public_subnet_ids
  certificate_arn     = var.certificate_arn
  deletion_protection = var.deletion_protection
}

module "app" {
  source                = "./modules/app-tier"
  name                  = local.name
  vpc_id                = module.vpc.vpc_id
  app_subnet_ids        = module.vpc.app_subnet_ids
  alb_security_group_id = module.web.alb_security_group_id
  target_group_arn      = module.web.target_group_arn
  instance_type         = var.app_instance_type
  min_size              = var.app_min_size
  max_size              = var.app_max_size
  region                = var.aws_region
  db_endpoint           = module.data.db_endpoint
  db_name               = module.data.db_name
  db_secret_arn         = module.data.db_secret_arn
}

# Reglas entre capas app <-> data (definidas aquí para evitar dependencias circulares entre módulos).
resource "aws_vpc_security_group_ingress_rule" "db_from_app" {
  security_group_id            = module.data.db_security_group_id
  referenced_security_group_id = module.app.app_security_group_id
  ip_protocol                  = "tcp"
  from_port                    = module.data.db_port
  to_port                      = module.data.db_port
  description                  = "PostgreSQL desde la capa app"
}

resource "aws_vpc_security_group_egress_rule" "app_to_db" {
  security_group_id            = module.app.app_security_group_id
  referenced_security_group_id = module.data.db_security_group_id
  ip_protocol                  = "tcp"
  from_port                    = module.data.db_port
  to_port                      = module.data.db_port
  description                  = "PostgreSQL hacia la capa datos"
}

# ---------------- Alarmas por capa ----------------
resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${local.name}-alb-target-5xx"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 5
  datapoints_to_alarm = 3
  threshold           = 10
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  dimensions = {
    LoadBalancer = module.web.alb_arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "unhealthy_hosts" {
  alarm_name          = "${local.name}-unhealthy-hosts"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  dimensions = {
    LoadBalancer = module.web.alb_arn_suffix
    TargetGroup  = module.web.target_group_arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "db_cpu" {
  alarm_name          = "${local.name}-db-cpu"
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  dimensions = {
    DBInstanceIdentifier = module.data.db_identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "db_storage" {
  alarm_name          = "${local.name}-db-free-storage"
  namespace           = "AWS/RDS"
  metric_name         = "FreeStorageSpace"
  statistic           = "Minimum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 2147483648 # 2 GiB
  comparison_operator = "LessThanThreshold"
  dimensions = {
    DBInstanceIdentifier = module.data.db_identifier
  }
}
