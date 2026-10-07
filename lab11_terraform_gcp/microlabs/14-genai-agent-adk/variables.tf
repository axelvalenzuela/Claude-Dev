variable "model" {
  type    = string
  default = "gemini-2.5-flash"
}

variable "vertex_location" {
  type    = string
  default = "global"
}

variable "invoker_members" {
  description = "Quién puede hablar con el agente, p. ej. [\"user:tu@correo\"]."
  type        = list(string)
}

variable "sample_orders" {
  description = "Pedidos de ejemplo que consulta la herramienta consultar_pedido."
  type = map(object({
    estado           = string
    total_mxn        = number
    entrega_estimada = string
    categoria        = string
  }))
  default = {
    "PED-1001" = { estado = "enviado", total_mxn = 2499.0, entrega_estimada = "2026-10-12", categoria = "electronica" }
    "PED-1002" = { estado = "entregado", total_mxn = 899.0, entrega_estimada = "2026-10-03", categoria = "ropa" }
    "PED-1003" = { estado = "retrasado", total_mxn = 5400.0, entrega_estimada = "2026-10-20", categoria = "hogar" }
  }
}
