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

variable "tags" {
  type    = map(string)
  default = {}
}

locals {
  vol_defs = {
    data   = { size = var.volumes.data_gb, device = "/dev/sdf", iops = var.volumes.data_iops, throughput = var.volumes.data_throughput }
    log    = { size = var.volumes.log_gb, device = "/dev/sdg", iops = var.volumes.log_iops, throughput = var.volumes.log_throughput }
    shared = { size = var.volumes.shared_gb, device = "/dev/sdh", iops = 3000, throughput = 125 }
    backup = { size = var.volumes.backup_gb, device = "/dev/sdi", iops = 3000, throughput = 125 }
  }

  node_volumes = {
    for pair in setproduct(keys(var.nodes), keys(local.vol_defs)) :
    "${pair[0]}-${pair[1]}" => { node = pair[0], vol = pair[1] }
  }
}

resource "aws_instance" "hana" {
  for_each = var.nodes

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
    Name = "${var.name_prefix}-hana-${each.key}"
    Role = "hana-${each.key}"
  })

  lifecycle {
    ignore_changes = [ami]
  }
}

resource "aws_ebs_volume" "hana" {
  for_each = local.node_volumes

  availability_zone = var.nodes[each.value.node].az
  size              = local.vol_defs[each.value.vol].size
  type              = "gp3"
  iops              = local.vol_defs[each.value.vol].iops
  throughput        = local.vol_defs[each.value.vol].throughput
  encrypted         = true
  kms_key_id        = var.kms_key_arn

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-hana-${each.value.node}-${each.value.vol}"
    Role = "hana-${each.value.vol}"
  })
}

resource "aws_volume_attachment" "hana" {
  for_each = local.node_volumes

  device_name = local.vol_defs[each.value.vol].device
  volume_id   = aws_ebs_volume.hana[each.key].id
  instance_id = aws_instance.hana[each.value.node].id
}

output "instance_ids" {
  value = { for k, i in aws_instance.hana : k => i.id }
}

output "private_ips" {
  value = { for k, i in aws_instance.hana : k => i.private_ip }
}
