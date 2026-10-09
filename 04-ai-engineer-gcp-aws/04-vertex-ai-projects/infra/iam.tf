# Una cuenta de servicio dedicada para la Function, Cloud Run y los scripts
# desplegados, con SOLO los permisos que necesitan (mínimo privilegio).
# Nunca uses la cuenta de servicio por defecto de Compute: tiene rol Editor en todo el proyecto.
resource "google_service_account" "agente" {
  account_id   = "agente-migracion"
  display_name = "Agente de migración SAS (el curso)"
}

locals {
  roles_proyecto = [
    "roles/aiplatform.user",        # llamar a Gemini y embeddings
    "roles/bigquery.jobUser",       # ejecutar consultas y cargas (el acceso a datos va en el dataset)
    "roles/logging.logWriter",      # escribir logs
    "roles/eventarc.eventReceiver", # recibir eventos de Storage (ejercicio 18)
    "roles/run.invoker",            # Eventarc invoca la Function con esta cuenta (ejercicio 18)
  ]
}

resource "google_project_iam_member" "agente" {
  for_each = toset(local.roles_proyecto)

  project = var.proyecto
  role    = each.value
  member  = "serviceAccount:${google_service_account.agente.email}"
}

# Permisos sobre recursos concretos, no sobre todo el proyecto.
resource "google_bigquery_dataset_iam_member" "agente_editor" {
  dataset_id = google_bigquery_dataset.migracion.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.agente.email}"
}

resource "google_storage_bucket_iam_member" "agente_objetos" {
  bucket = google_storage_bucket.migracion.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.agente.email}"
}

# Error clásico del ejercicio 18: para que un evento de Storage llegue a Eventarc, el
# agente de servicio de Cloud Storage necesita publicar en Pub/Sub.
data "google_storage_project_service_account" "gcs" {
  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "gcs_publica_eventos" {
  project = var.proyecto
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs.email_address}"
}
