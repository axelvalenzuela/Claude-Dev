output "chat_url" {
  value = module.chat_fn.uri
}

output "template" {
  value = google_model_armor_template.this.id
}
