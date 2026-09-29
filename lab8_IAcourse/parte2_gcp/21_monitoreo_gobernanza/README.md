# 21 — Monitoreo, costos y gobernanza

**Qué aprendes:** saber cuánto gasta, qué tan rápido responde y qué tan seguro es tu sistema de IA,
con datos, y poner reglas (guardrails) alrededor del modelo.

## Conceptos

| Pregunta en producción | Cómo se responde aquí |
|---|---|
| ¿Cuánto gastamos y en qué agente? | Cada llamada se registra (tokens, costo, latencia, rol, modelo) → [reporte_costos.py](reporte_costos.py) |
| ¿Dónde veo los logs? | Logs JSON con `severity` → Cloud Logging los indexa por campo ([comun/observabilidad.py](../comun/observabilidad.py)) |
| ¿Tableros e historial? | `--bigquery` carga el registro a `auditoria_llm` (particionada por día) |
| ¿Mandamos datos sensibles al modelo? | Redacción antes de enviar ([comun/guardrails.py](../comun/guardrails.py)) |
| ¿Ejecutamos código peligroso? | Revisión AST + proceso aparte + timeout; sandbox en producción |
| ¿Nos avisa si se dispara el gasto? | Presupuesto con alertas ([infra/presupuesto.tf](../../infra/presupuesto.tf)) |
| ¿La calidad bajó? | Golden set + quality gate (lab 16), tasa de `REQUIERE_REVISION` |

**Gobernanza** (lo que un Senior debe mencionar): cuentas de servicio con mínimo privilegio,
auditoría de cada llamada, versionado de prompts junto al código (git), revisión humana de lo
que no se puede validar automáticamente, plan para retiro de modelos, y datos que no salen del
perímetro de GCP (Vertex AI no entrena con tus datos).

## Para la entrevista

- *"¿Qué métricas monitoreas en un sistema de agentes?"* → costo por tarea y por agente, tokens,
  latencia p50/p95, tasa de error del API (429/5xx), intentos promedio hasta aprobar, tasa de
  revisión humana, y métricas de calidad del golden set.

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
