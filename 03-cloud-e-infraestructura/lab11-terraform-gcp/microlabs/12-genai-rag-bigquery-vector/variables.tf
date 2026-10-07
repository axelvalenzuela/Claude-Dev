variable "bq_location" {
  description = "Ubicación del dataset y de la conexión (US o una región)."
  type        = string
  default     = "US"
}

variable "embedding_endpoint" {
  description = "Modelo de embeddings de Vertex AI. Multilingüe para documentos en español."
  type        = string
  default     = "text-multilingual-embedding-002"
}

variable "model" {
  description = "Modelo que redacta la respuesta."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "vertex_location" {
  type    = string
  default = "global"
}

variable "top_k" {
  description = "Chunks recuperados por pregunta (más = más contexto y más tokens)."
  type        = number
  default     = 4
}

variable "max_distance" {
  description = "Distancia coseno máxima para aceptar un chunk (0 = idéntico, 2 = opuesto). Filtra contexto irrelevante."
  type        = number
  default     = 0.6
}

variable "invoker_members" {
  description = "Quién puede consultar el servicio, p. ej. [\"user:tu@correo\"]."
  type        = list(string)
}
