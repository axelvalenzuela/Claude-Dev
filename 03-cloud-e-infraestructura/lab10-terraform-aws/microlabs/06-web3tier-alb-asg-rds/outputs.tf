output "app_url" {
  value = "http://${module.web.alb_dns_name}"
}

output "target_group_arn" {
  value = module.web.target_group_arn
}

output "asg_name" {
  value = module.app.asg_name
}

output "db_endpoint" {
  value = module.data.db_endpoint
}

output "db_secret_arn" {
  value = module.data.db_secret_arn
}

output "vpc_id" {
  value = module.vpc.vpc_id
}
