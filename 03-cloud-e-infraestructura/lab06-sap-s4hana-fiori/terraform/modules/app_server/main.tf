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

variable "delete_volumes_on_termination" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}

module "ec2" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 5.0"

  for_each = var.servers

  name = "${var.name_prefix}-app-${each.key}"

  ami                    = var.ami_id
  ignore_ami_changes     = true
  instance_type          = var.instance_type
  subnet_id              = each.value.subnet_id
  vpc_security_group_ids = var.security_group_ids
  iam_instance_profile   = var.instance_profile_name
  ebs_optimized          = true
  monitoring             = true

  metadata_options = {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device = [
    {
      volume_type = "gp3"
      volume_size = var.root_gb
      encrypted   = true
      kms_key_id  = var.kms_key_arn
    }
  ]

  ebs_block_device = [
    {
      device_name           = "/dev/sdf"
      volume_type           = "gp3"
      volume_size           = var.usr_sap_gb
      encrypted             = true
      kms_key_id            = var.kms_key_arn
      delete_on_termination = var.delete_volumes_on_termination
      tags                  = merge(var.tags, { Role = "app-usr-sap" })
    }
  ]

  tags = merge(var.tags, { Role = "app-${each.key}" })
}

output "instance_ids" {
  value = { for k, m in module.ec2 : k => m.id }
}

output "private_ips" {
  value = { for k, m in module.ec2 : k => m.private_ip }
}

output "usr_sap_volume_ids" {
  value = {
    for k, m in module.ec2 : k => one([for b in m.ebs_block_device : b.volume_id if b.device_name == "/dev/sdf"])
  }
}
