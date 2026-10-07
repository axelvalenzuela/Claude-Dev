# Bucket de trabajo: entrada/ (programas .sas), resultados/ (JSON de la Function),
# tmp/ (archivos temporales de Dataflow).
resource "google_storage_bucket" "migracion" {
  name     = "${var.proyecto}-migracion-sas"
  location = var.region

  uniform_bucket_level_access = true       # permisos solo por IAM, sin ACLs por objeto
  public_access_prevention    = "enforced" # imposible hacerlo público por accidente
  force_destroy               = true       # es un lab: permite destruirlo aunque tenga archivos

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete" # borra archivos de más de 30 días: el costo de almacenamiento no crece solo
    }
  }

  labels = local.etiquetas

  depends_on = [google_project_service.apis]
}
