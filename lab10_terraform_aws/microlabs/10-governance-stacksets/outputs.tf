output "stack_set_name" {
  value = aws_cloudformation_stack_set.baseline.name
}

output "stack_set_id" {
  value = aws_cloudformation_stack_set.baseline.stack_set_id
}

output "central_event_bus_arn" {
  value = aws_cloudwatch_event_bus.security.arn
}
