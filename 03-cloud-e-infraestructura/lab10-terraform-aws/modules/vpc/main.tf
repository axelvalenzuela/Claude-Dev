# Módulo: VPC multi-AZ de 3 capas.
#   public  -> ALB / NAT Gateway (ruta a Internet Gateway)
#   app     -> cómputo (EC2/ECS/Lambda) con salida vía NAT opcional
#   data    -> bases de datos, SIN ruta a Internet (aisladas)
# WAF Confiabilidad: multi-AZ. Seguridad: SG por defecto cerrado, flow logs, VPC endpoints.
# WAF Costos: single_nat_gateway=true en labs (en producción un NAT por AZ).

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, var.az_count)

  public_cidrs = [for i in range(var.az_count) : cidrsubnet(var.cidr_block, 8, i)]
  app_cidrs    = [for i in range(var.az_count) : cidrsubnet(var.cidr_block, 8, 10 + i)]
  data_cidrs   = [for i in range(var.az_count) : cidrsubnet(var.cidr_block, 8, 20 + i)]

  nat_count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : var.az_count) : 0
}

resource "aws_vpc" "this" {
  cidr_block           = var.cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = merge(var.tags, { Name = var.name })
}

# Cierra el security group por defecto (CIS AWS Foundations 5.4).
resource "aws_default_security_group" "this" {
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.name}-default-closed" })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.name}-igw" })
}

# ---------------- Subnets ----------------
resource "aws_subnet" "public" {
  count             = var.az_count
  vpc_id            = aws_vpc.this.id
  cidr_block        = local.public_cidrs[count.index]
  availability_zone = local.azs[count.index]
  tags              = merge(var.tags, { Name = "${var.name}-public-${local.azs[count.index]}", Tier = "public" })
}

resource "aws_subnet" "app" {
  count             = var.az_count
  vpc_id            = aws_vpc.this.id
  cidr_block        = local.app_cidrs[count.index]
  availability_zone = local.azs[count.index]
  tags              = merge(var.tags, { Name = "${var.name}-app-${local.azs[count.index]}", Tier = "app" })
}

resource "aws_subnet" "data" {
  count             = var.az_count
  vpc_id            = aws_vpc.this.id
  cidr_block        = local.data_cidrs[count.index]
  availability_zone = local.azs[count.index]
  tags              = merge(var.tags, { Name = "${var.name}-data-${local.azs[count.index]}", Tier = "data" })
}

# ---------------- NAT ----------------
resource "aws_eip" "nat" {
  count  = local.nat_count
  domain = "vpc"
  tags   = merge(var.tags, { Name = "${var.name}-nat-eip-${count.index}" })
}

resource "aws_nat_gateway" "this" {
  count         = local.nat_count
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  tags          = merge(var.tags, { Name = "${var.name}-nat-${count.index}" })
  depends_on    = [aws_internet_gateway.this]
}

# ---------------- Route tables ----------------
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.name}-public-rt" })
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public" {
  count          = var.az_count
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "app" {
  count  = var.az_count
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.name}-app-rt-${local.azs[count.index]}" })
}

resource "aws_route" "app_nat" {
  count                  = local.nat_count > 0 ? var.az_count : 0
  route_table_id         = aws_route_table.app[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this[var.single_nat_gateway ? 0 : count.index].id
}

resource "aws_route_table_association" "app" {
  count          = var.az_count
  subnet_id      = aws_subnet.app[count.index].id
  route_table_id = aws_route_table.app[count.index].id
}

resource "aws_route_table" "data" {
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.name}-data-rt-isolated" })
}

resource "aws_route_table_association" "data" {
  count          = var.az_count
  subnet_id      = aws_subnet.data[count.index].id
  route_table_id = aws_route_table.data.id
}

# ---------------- VPC Endpoints ----------------
# Gateway endpoints (gratuitos): S3 y DynamoDB sin pasar por NAT.
resource "aws_vpc_endpoint" "gateway" {
  for_each          = var.enable_gateway_endpoints ? toset(["s3", "dynamodb"]) : toset([])
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${var.region}.${each.key}"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = concat(aws_route_table.app[*].id, [aws_route_table.data.id])
  tags              = merge(var.tags, { Name = "${var.name}-${each.key}-gw-endpoint" })
}

resource "aws_security_group" "endpoints" {
  count       = length(var.interface_endpoints) > 0 ? 1 : 0
  name        = "${var.name}-vpce"
  description = "HTTPS hacia interface endpoints desde la VPC"
  vpc_id      = aws_vpc.this.id
  tags        = var.tags
}

resource "aws_vpc_security_group_ingress_rule" "endpoints_https" {
  count             = length(var.interface_endpoints) > 0 ? 1 : 0
  security_group_id = aws_security_group.endpoints[0].id
  cidr_ipv4         = var.cidr_block
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  description       = "HTTPS desde la VPC"
}

# Interface endpoints (con costo por hora/AZ): p. ej. ["secretsmanager", "ssm", "ssmmessages", "ec2messages", "bedrock-runtime"]
resource "aws_vpc_endpoint" "interface" {
  for_each            = toset(var.interface_endpoints)
  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.region}.${each.key}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.app[*].id
  security_group_ids  = [aws_security_group.endpoints[0].id]
  private_dns_enabled = true
  tags                = merge(var.tags, { Name = "${var.name}-${each.key}-endpoint" })
}

# ---------------- Flow logs ----------------
resource "aws_cloudwatch_log_group" "flow_logs" {
  count             = var.enable_flow_logs ? 1 : 0
  name              = "/vpc/${var.name}/flow-logs"
  retention_in_days = var.flow_logs_retention_days
  kms_key_id        = var.kms_key_arn
  tags              = var.tags
}

data "aws_iam_policy_document" "flow_logs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "flow_logs" {
  count              = var.enable_flow_logs ? 1 : 0
  name               = "${var.name}-flow-logs"
  assume_role_policy = data.aws_iam_policy_document.flow_logs_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "flow_logs" {
  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "flow_logs" {
  count  = var.enable_flow_logs ? 1 : 0
  name   = "flow-logs"
  role   = aws_iam_role.flow_logs[0].id
  policy = data.aws_iam_policy_document.flow_logs.json
}

resource "aws_flow_log" "this" {
  count           = var.enable_flow_logs ? 1 : 0
  vpc_id          = aws_vpc.this.id
  traffic_type    = "REJECT"
  log_destination = aws_cloudwatch_log_group.flow_logs[0].arn
  iam_role_arn    = aws_iam_role.flow_logs[0].arn
  tags            = var.tags
}
