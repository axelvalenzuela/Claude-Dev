output "staging_subnet_id" {
  value = aws_subnet.staging.id
}

output "replication_security_group_id" {
  value = aws_security_group.replication.id
}

output "target_subnet_ids" {
  value = module.vpc.app_subnet_ids
}

output "target_security_group_id" {
  value = aws_security_group.target.id
}

output "agent_installer_role_arn" {
  value = aws_iam_role.agent_installer.arn
}

output "ebs_kms_key_arn" {
  value = module.kms.key_arn
}
