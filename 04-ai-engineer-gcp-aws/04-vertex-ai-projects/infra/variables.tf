variable "proyecto" {
  description = "ID del proyecto de GCP (gcloud config get-value project)"
  type        = string
}

variable "region" {
  description = "Región para Storage, Cloud Run y Cloud Functions"
  type        = string
  default     = "us-central1"
}

variable "ubicacion_bigquery" {
  description = "Ubicación del dataset. US (multi-región) es la más común y compatible."
  type        = string
  default     = "US"
}

variable "dataset" {
  description = "Nombre del dataset de BigQuery (debe coincidir con BQ_DATASET en 04-vertex-ai-projects/.env)"
  type        = string
  default     = "migracion_sas"
}

variable "billing_account_id" {
  description = "ID de la cuenta de facturación (XXXXXX-XXXXXX-XXXXXX) para crear el presupuesto. Vacío = no se crea."
  type        = string
  default     = ""
}

variable "presupuesto_mensual" {
  description = "Monto del presupuesto mensual, en la moneda de tu cuenta de facturación"
  type        = number
  default     = 10
}

variable "moneda_presupuesto" {
  description = "Debe ser la MISMA moneda de tu cuenta de facturación (USD, MXN...). Si no, el apply falla."
  type        = string
  default     = "USD"
}
