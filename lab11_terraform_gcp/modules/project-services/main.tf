# Módulo: habilita APIs del proyecto. disable_on_destroy = false evita romper otros labs que las usan.

resource "google_project_service" "this" {
  for_each                   = toset(var.services)
  project                    = var.project_id
  service                    = each.value
  disable_on_destroy         = false
  disable_dependent_services = false
}

# Las APIs recién habilitadas tardan en propagarse; esperar evita errores 403 "API not enabled".
resource "time_sleep" "propagation" {
  depends_on      = [google_project_service.this]
  create_duration = var.propagation_wait
}
