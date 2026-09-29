# 21 — Instrucciones

## Paso 1 — Guardrails

```bash
python 21_monitoreo_gobernanza/demo_guardrails.py
```

## Paso 2 — Reporte de costos

Corre antes algunos labs (11–19) para tener registros, y luego:

```bash
python 21_monitoreo_gobernanza/reporte_costos.py
python 21_monitoreo_gobernanza/reporte_costos.py --programas 5000
```

Los registros viven en `.registros/llamadas.jsonl` (una línea JSON por llamada). Bórralo para empezar de cero.

## Paso 3 — Ver los logs en vivo

Pon `LOG_NIVEL=INFO` en `.env` y corre cualquier lab: cada llamada imprime una línea JSON en
stderr. Así se ven en Cloud Logging cuando corren en Cloud Run o Functions.

Filtros útiles en **Logging > Explorador de registros** (real, labs 18–19 desplegados):

```
jsonPayload.message="llamada_llm"
jsonPayload.rol="convertidor" AND jsonPayload.costo_usd > 0.01
severity>=WARNING
```

## Paso 4 — Auditoría en BigQuery (real)

```bash
python 21_monitoreo_gobernanza/reporte_costos.py --bigquery
```

Luego consulta `auditoria_llm` (ejemplos en [17_bigquery/INSTRUCCIONES.md](../17_bigquery/INSTRUCCIONES.md)).
Idea para producción: una **métrica basada en logs** sobre `costo_usd` + una **política de
alertas** en Cloud Monitoring si el gasto por hora supera un umbral.

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| "No hay registros" | No has corrido labs | Corre 11–19 primero |
| Registros de simulado y real mezclados | Mismo archivo | El reporte separa por `modo`; o borra `.registros/` |
| `--bigquery`: `Not found: Table auditoria_llm` | Falta `terraform apply` | Aplica Terraform |
| La redacción no detecta un dato | Patrón no cubierto | Agrega la regex a `_PATRONES_SENSIBLES`; en producción usa **Sensitive Data Protection (DLP)** |
| Código legítimo bloqueado | Módulo no permitido | Agrega el módulo a `MODULOS_PERMITIDOS` si es seguro |

## Retos

1. Agrega al reporte la latencia p95.
2. Agrega el patrón de número telefónico de 10 dígitos a los datos sensibles y un test en `tests/test_guardrails.py`.
