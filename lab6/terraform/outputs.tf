output "vpc_id" {
  value = module.network.vpc_id
}

output "hana_private_ips" {
  value       = module.hana_nodes.private_ips
  description = "IPs privadas de los nodos HANA (primary y, con HA, secondary)."
}

output "app_private_ips" {
  value = module.app_server.private_ips
}

output "backup_bucket" {
  value = module.backup_storage.bucket_name
}

output "kms_key_arn" {
  value = module.security.kms_key_arn
}

output "ssm_connect_hint" {
  value       = "aws ssm start-session --target <instance-id>"
  description = "Acceso administrativo sin SSH ni llaves."
}

output "region" {
  value = var.region
}

output "sap_instance_number" {
  value = var.sap_instance_number
}

output "hana_instance_ids" {
  value = module.hana_nodes.instance_ids
}

output "hana_volume_ids" {
  value = module.hana_nodes.volume_ids
}

output "app_instance_ids" {
  value = module.app_server.instance_ids
}

output "app_usr_sap_volume_ids" {
  value = module.app_server.usr_sap_volume_ids
}
