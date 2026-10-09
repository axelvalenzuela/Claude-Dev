# APIs que usan los labs. Habilitarlas no cuesta: se paga solo por lo que se usa.
locals {
  apis = [
    "aiplatform.googleapis.com",       # Vertex AI (Gemini + embeddings)
    "bigquery.googleapis.com",         # ejercicio 17
    "storage.googleapis.com",          # ejercicios 18 y 20
    "cloudfunctions.googleapis.com",   # ejercicio 18
    "eventarc.googleapis.com",         # disparador Storage -> Function
    "pubsub.googleapis.com",           # Eventarc lo usa por dentro
    "run.googleapis.com",              # ejercicio 19 (y Functions 2ª gen corren sobre Cloud Run)
    "cloudbuild.googleapis.com",       # construye las imágenes al desplegar con --source
    "artifactregistry.googleapis.com", # guarda esas imágenes
    "logging.googleapis.com",          # ejercicio 21
    "billingbudgets.googleapis.com",   # presupuesto y alertas
    "dataflow.googleapis.com",         # ejercicio 20 (solo si corres en Dataflow)
  ]
}

resource "google_project_service" "apis" {
  for_each = toset(local.apis)

  service            = each.value
  disable_on_destroy = false # destruir el lab no debe apagar APIs que otros usen
}
