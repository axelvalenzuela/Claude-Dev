# APIs que usan los labs. Habilitarlas no cuesta: se paga solo por lo que se usa.
locals {
  apis = [
    "aiplatform.googleapis.com",       # Vertex AI (Gemini + embeddings)
    "bigquery.googleapis.com",         # lab 17
    "storage.googleapis.com",          # labs 18 y 20
    "cloudfunctions.googleapis.com",   # lab 18
    "eventarc.googleapis.com",         # disparador Storage -> Function
    "pubsub.googleapis.com",           # Eventarc lo usa por dentro
    "run.googleapis.com",              # lab 19 (y Functions 2ª gen corren sobre Cloud Run)
    "cloudbuild.googleapis.com",       # construye las imágenes al desplegar con --source
    "artifactregistry.googleapis.com", # guarda esas imágenes
    "logging.googleapis.com",          # lab 21
    "billingbudgets.googleapis.com",   # presupuesto y alertas
    "dataflow.googleapis.com",         # lab 20 (solo si corres en Dataflow)
  ]
}

resource "google_project_service" "apis" {
  for_each = toset(local.apis)

  service            = each.value
  disable_on_destroy = false # destruir el lab no debe apagar APIs que otros usen
}
