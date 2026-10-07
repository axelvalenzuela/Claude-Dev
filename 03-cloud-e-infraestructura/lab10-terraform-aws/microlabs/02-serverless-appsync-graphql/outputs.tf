output "graphql_url" {
  value = aws_appsync_graphql_api.this.uris["GRAPHQL"]
}

output "realtime_url" {
  value = aws_appsync_graphql_api.this.uris["REALTIME"]
}

output "api_id" {
  value = aws_appsync_graphql_api.this.id
}

output "user_pool_id" {
  value = aws_cognito_user_pool.this.id
}

output "user_pool_client_id" {
  value = aws_cognito_user_pool_client.this.id
}
