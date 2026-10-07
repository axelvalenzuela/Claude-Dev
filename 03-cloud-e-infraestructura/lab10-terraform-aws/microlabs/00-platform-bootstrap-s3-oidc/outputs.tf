output "tf_state_bucket" {
  description = "Valor para la variable de GitLab TF_STATE_BUCKET."
  value       = module.state_bucket.bucket_id
}

output "tf_state_kms_key_arn" {
  value = module.state_key.key_arn
}

output "aws_plan_role_arn" {
  description = "Valor para la variable de GitLab AWS_PLAN_ROLE_ARN."
  value       = aws_iam_role.plan.arn
}

output "aws_apply_role_arn" {
  description = "Valor para la variable de GitLab AWS_APPLY_ROLE_ARN."
  value       = aws_iam_role.apply.arn
}

output "ci_permissions_boundary_arn" {
  value = aws_iam_policy.boundary.arn
}
