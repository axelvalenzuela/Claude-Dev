output "neptune_endpoint" {
  value = aws_neptune_cluster.this.endpoint
}

output "neptune_reader_endpoint" {
  value = aws_neptune_cluster.this.reader_endpoint
}

output "client_function" {
  value = module.client_fn.function_name
}

output "load_bucket" {
  value = module.load_bucket.bucket_id
}
