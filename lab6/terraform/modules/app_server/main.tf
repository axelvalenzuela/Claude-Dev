variable "name_prefix" {
  type = string
}

variable "servers" {
  type = map(object({
    subnet_id = string
    az        = string
  }))
  description = "Servidores de aplicacion ABAP (p. ej. ascs-pas, aas1)."
}

variable "ami_id" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "security_group_ids" {
  type = list(string)
}

variable "instance_profile_name" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

variable "root_gb" {
  type    = number
  default = 100
}

variable "usr_sap_gb" {
  type    = number
  default = 100
}

variable "tags" {
  type    = map(string)
  default = {}
}

resource "aws_instance" "app" {
  for_each = var.servers

  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = each.value.subnet_id
  vpc_security_group_ids = var.security_group_ids
  iam_instance_profile   = var.instance_profile_name
  ebs_optimized          = true
  monitoring             = true

  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = var.root_gb
    encrypted   = true
    kms_key_id  = var.kms_key_arn
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-app-${each.key}"
    Role = "app-${each.key}"
  })

  lifecycle {
    ignore_changes = [ami]
  }
}

resource "aws_ebs_volume" "usr_sap" {
  for_each = var.servers

  availability_zone = each.value.az
  size              = var.usr_sap_gb
  type              = "gp3"
  encrypted         = true
  kms_key_id        = var.kms_key_arn

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-app-${each.key}-usrsap"
    Role = "app-usr-sap"
  })
}

resource "aws_volume_attachment" "usr_sap" {
  for_each = var.servers

  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.usr_sap[each.key].id
  instance_id = aws_instance.app[each.key].id
}

output "instance_ids" {
  value = { for k, i in aws_instance.app : k => i.id }
}

output "private_ips" {
  value = { for k, i in aws_instance.app : k => i.private_ip }
}
