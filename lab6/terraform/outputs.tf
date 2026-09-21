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
