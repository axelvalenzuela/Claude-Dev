# Módulo: Cloud KMS keyring + llave simétrica con rotación.
# Los keyrings NO se pueden borrar en GCP: el sufijo aleatorio permite recrear el lab sin colisiones.

resource "random_id" "suffix" {
  byte_length = 2
}

resource "google_kms_key_ring" "this" {
  name     = "${var.name}-${random_id.suffix.hex}"
  project  = var.project_id
  location = var.location
}

resource "google_kms_crypto_key" "this" {
  name            = var.name
  key_ring        = google_kms_key_ring.this.id
  rotation_period = var.rotation_period
  purpose         = "ENCRYPT_DECRYPT"

  # 24 h de espera antes de destruir material de llave (protege contra borrados accidentales)
  destroy_scheduled_duration = "86400s"

  lifecycle {
    prevent_destroy = false
  }
}

# Agentes de servicio (GCS, BigQuery, Pub/Sub, Cloud SQL...) que cifran con esta llave.
resource "google_kms_crypto_key_iam_member" "encrypters" {
  for_each      = toset(var.encrypter_members)
  crypto_key_id = google_kms_crypto_key.this.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
}
