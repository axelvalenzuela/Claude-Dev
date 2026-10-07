variable "name_prefix" {
  type        = string
  description = "Prefijo para nombrar recursos."
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR de la VPC."
}

variable "azs" {
  type        = list(string)
  description = "Zonas de disponibilidad, una por subred privada."
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "CIDRs de subredes privadas (HANA y aplicacion), una por AZ."
}

variable "public_subnet_cidr" {
  type        = string
  description = "CIDR de la subred publica (solo NAT)."
}

variable "tags" {
  type    = map(string)
  default = {}
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.name_prefix}-vpc"
  cidr = var.vpc_cidr
  azs  = var.azs

  private_subnets = var.private_subnet_cidrs
  public_subnets  = [var.public_subnet_cidr]

  enable_nat_gateway      = true
  single_nat_gateway      = true
  enable_dns_hostnames    = true
  enable_dns_support      = true
  map_public_ip_on_launch = false

  tags = var.tags
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnet_ids" {
  value = module.vpc.private_subnets
}

output "public_subnet_id" {
  value = module.vpc.public_subnets[0]
}
