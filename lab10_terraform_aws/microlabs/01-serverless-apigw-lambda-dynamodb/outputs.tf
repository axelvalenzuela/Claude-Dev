output "api_url" {
  value = aws_api_gateway_stage.this.invoke_url
}

output "api_key_id" {
  description = "Obtén el valor con: aws apigateway get-api-key --api-key <id> --include-value"
  value       = aws_api_gateway_api_key.client.id
}

output "user_pool_id" {
  value = aws_cognito_user_pool.this.id
}

output "user_pool_client_id" {
  value = aws_cognito_user_pool_client.this.id
}

output "access_log_group" {
  value = aws_cloudwatch_log_group.access.name
}

output "api_name" {
  value = aws_api_gateway_rest_api.this.name
}

output "stage_name" {
  value = aws_api_gateway_stage.this.stage_name
}

output "table_name" {
  value = module.table.table_name
}
