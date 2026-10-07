output "chat_endpoint" {
  value = "${aws_apigatewayv2_api.this.api_endpoint}/chat"
}

output "user_pool_id" {
  value = aws_cognito_user_pool.this.id
}

output "user_pool_client_id" {
  value = aws_cognito_user_pool_client.this.id
}

output "history_table" {
  value = module.history.table_name
}

output "guardrail_id" {
  value = aws_bedrock_guardrail.this.guardrail_id
}
