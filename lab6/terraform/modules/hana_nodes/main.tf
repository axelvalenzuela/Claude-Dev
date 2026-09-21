variable "name_prefix" {
  type = string
}

variable "nodes" {
  type = map(object({
    subnet_id = string
    az        = string
  }))
  description = "Nodos HANA: primary y, si hay HA, secondary (en otra AZ)."
}

variable "ami_id" {
  type = string
}

variable "instance_type" {
  type        = string
  description = "Tipo de instancia certificado para SAP HANA (verificar en el directorio de plataformas certificadas)."
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

variable "volumes" {
  type = object({
    data_gb         = number
    log_gb          = number
    shared_gb       = number
    backup_gb       = number
    data_iops       = number
    data_throughput = number
    log_iops        = number
    log_throughput  = number
  })
  description = "Tamano y rendimiento de los volumenes de HANA."
}

variable "delete_volumes_on_termination" {
  type        = bool
  default     = false
  description = "false conserva los discos de datos si se destruye la instancia (recomendado fuera de dev)."
}

variable "tags" {
  type    = map(string)
  default = {}
}

locals {
  # Layout SAP HANA: un volumen por funcion.
  vol_defs = {
    data   = { size = var.volumes.data_gb, device = "/dev/sdf", iops = var.volumes.data_iops, throughput = var.volumes.data_throughput }
    log    = { size = var.volumes.log_gb, device = "/dev/sdg", iops = var.volumes.log_iops, throughput = var.volumes.log_throughput }
    shared = { size = var.volumes.shared_gb, device = "/dev/sdh", iops = 3000, throughput = 125 }
    backup = { size = var.volumes.backup_gb, device = "/dev/sdi", iops = 3000, throughput = 125 }
  }

  ebs_block_devices = [
    for name, v in local.vol_defs : {
      device_name           = v.device
      volume_type           = "gp3"
      volume_size           = v.size
      iops                  = v.iops
      throughput            = v.throughput
      encrypted             = true
      kms_key_id            = var.kms_key_arn
      delete_on_termination = var.delete_volumes_on_termination
      tags                  = merge(var.tags, { Role = "hana-${name}" })
    }
  ]
}

module "ec2" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 5.0"

  for_each = var.nodes

  name = "${var.name_prefix}-hana-${each.key}"

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

  ebs_block_device = local.ebs_block_devices

  tags = merge(var.tags, { Role = "hana-${each.key}" })
}

output "instance_ids" {
  value = { for k, m in module.ec2 : k => m.id }
}

output "private_ips" {
  value = { for k, m in module.ec2 : k => m.private_ip }
}

output "volume_ids" {
  value = {
    for node, m in module.ec2 : node => {
      for name, v in local.vol_defs :
      name => one([for b in m.ebs_block_device : b.volume_id if b.device_name == v.device])
    }
  }
  description = "IDs de volumenes EBS por nodo y funcion (data/log/shared/backup)."
}
