output "documents_bucket" {
  value = module.documents.bucket_id
}

output "state_machine_arn" {
  value = aws_sfn_state_machine.pipeline.arn
}

output "results_table" {
  value = module.results.table_name
}
