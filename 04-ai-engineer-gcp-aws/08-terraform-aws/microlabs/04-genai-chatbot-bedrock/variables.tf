variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "aie"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "owner" {
  type = string
}

variable "cost_center" {
  type    = string
  default = "training"
}

variable "model_id" {
  description = "ID de modelo o inference profile de Bedrock habilitado en tu cuenta. Lista: aws bedrock list-foundation-models --by-output-modality TEXT"
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

variable "system_prompt" {
  type    = string
  default = "Eres un asistente técnico de AWS para estudiantes. Responde en español, de forma breve y precisa. Si no sabes algo, dilo."
}

variable "max_tokens" {
  type    = number
  default = 512
}

variable "history_turns" {
  description = "Turnos previos enviados como contexto (más turnos = más tokens = más costo)."
  type        = number
  default     = 6
}

variable "max_concurrency" {
  description = "Concurrencia reservada de la Lambda: tope duro de gasto en Bedrock."
  type        = number
  default     = 10
}

variable "throttle_rate_limit" {
  type    = number
  default = 10
}

variable "allowed_origins" {
  description = "Orígenes CORS permitidos (tu frontend)."
  type        = list(string)
  default     = ["http://localhost:8080"]
}

variable "hourly_output_token_alarm" {
  type    = number
  default = 200000
}
