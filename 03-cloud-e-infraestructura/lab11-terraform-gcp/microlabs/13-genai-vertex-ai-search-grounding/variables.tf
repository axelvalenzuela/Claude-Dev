variable "search_location" {
  description = "Ubicación de Vertex AI Search: global, us o eu (residencia de datos)."
  type        = string
  default     = "global"
}

variable "chunk_size" {
  description = "Tamaño de chunk en tokens (100-500) para el chunking por layout."
  type        = number
  default     = 500
}

variable "company_name" {
  description = "Contexto para el motor (mejora la relevancia de las respuestas)."
  type        = string
  default     = "NubeMX"
}

variable "model" {
  type    = string
  default = "gemini-2.5-flash"
}

variable "vertex_location" {
  type    = string
  default = "global"
}

variable "invoker_members" {
  description = "Quién puede consultar, p. ej. [\"user:tu@correo\"]."
  type        = list(string)
}
