output "key_id" {
  description = "projects/<p>/locations/<l>/keyRings/<r>/cryptoKeys/<k>"
  value       = google_kms_crypto_key.this.id
}

output "key_ring_id" {
  value = google_kms_key_ring.this.id
}
