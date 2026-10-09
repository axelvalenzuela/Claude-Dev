# Módulo: tabla DynamoDB on-demand con PITR, cifrado y TTL opcional.
# WAF Confiabilidad: PITR (restauración a cualquier segundo de los últimos 35 días).
# WAF Costos: PAY_PER_REQUEST (sin capacidad ociosa en labs / cargas impredecibles).

locals {
  key_definitions = concat(
    [{ name = var.hash_key, type = var.hash_key_type }],
    var.range_key == null ? [] : [{ name = var.range_key, type = var.range_key_type }],
    [for g in var.global_secondary_indexes : { name = g.hash_key, type = g.hash_key_type }],
    [for g in var.global_secondary_indexes : { name = g.range_key, type = g.range_key_type } if g.range_key != null],
  )
  # Agrupa por nombre para eliminar duplicados (una llave puede usarse en varios índices).
  attributes = { for a in local.key_definitions : a.name => a.type... }
}

resource "aws_dynamodb_table" "this" {
  name                        = var.name
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = var.hash_key
  range_key                   = var.range_key
  deletion_protection_enabled = var.deletion_protection
  stream_enabled              = var.stream_enabled
  stream_view_type            = var.stream_enabled ? "NEW_AND_OLD_IMAGES" : null

  dynamic "attribute" {
    for_each = local.attributes
    content {
      name = attribute.key
      type = attribute.value[0]
    }
  }

  dynamic "global_secondary_index" {
    for_each = var.global_secondary_indexes
    content {
      name            = global_secondary_index.value.name
      hash_key        = global_secondary_index.value.hash_key
      range_key       = global_secondary_index.value.range_key
      projection_type = global_secondary_index.value.projection_type
    }
  }

  dynamic "ttl" {
    for_each = var.ttl_attribute == null ? [] : [var.ttl_attribute]
    content {
      attribute_name = ttl.value
      enabled        = true
    }
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  tags = var.tags
}
