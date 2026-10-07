output "audit_bucket" {
  value = module.audit_bucket.bucket_id
}

output "cloudtrail_arn" {
  value = aws_cloudtrail.this.arn
}

output "guardduty_detector_id" {
  value = aws_guardduty_detector.this.id
}

output "findings_topic_arn" {
  value = module.alerts.topic_arn
}

output "rbac_role_arns" {
  value = { for k, r in aws_iam_role.rbac : k => r.arn }
}

output "developer_boundary_arn" {
  value = aws_iam_policy.developer_boundary.arn
}
