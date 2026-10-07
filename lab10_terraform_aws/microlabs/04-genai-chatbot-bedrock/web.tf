# Configuración del frontend de prueba (web/index.html). Se sirve localmente:
#   cd web && python -m http.server 8080   ->  http://localhost:8080
resource "local_file" "web_config" {
  filename = "${path.module}/web/config.js"
  content  = <<-EOT
    // Generado por Terraform: no editar.
    window.CHAT_CONFIG = {
      region: "${var.aws_region}",
      clientId: "${aws_cognito_user_pool_client.this.id}",
      endpoint: "${aws_apigatewayv2_api.this.api_endpoint}/chat"
    };
  EOT
}
