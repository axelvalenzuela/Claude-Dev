output "event_bus_name" {
  value = aws_cloudwatch_event_bus.orders.name
}

output "archive_name" {
  value = aws_cloudwatch_event_archive.orders.name
}

output "high_value_queue_url" {
  value = aws_sqs_queue.high_value.id
}

output "dlq_url" {
  value = aws_sqs_queue.dlq.id
}

output "processor_log_group" {
  value = module.processor.log_group_name
}

output "audit_log_group" {
  value = aws_cloudwatch_log_group.audit.name
}
