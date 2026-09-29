# 17 — Instrucciones

## Paso 1 — En simulado (SQLite local)

```bash
python 17_bigquery/sas_a_bigquery.py
```

Verás los 5 pasos; el SQL aprobado queda en `salida/resumen_ventas.sql`.

## Paso 2 — Crear la infraestructura (Terraform)

```bash
cd ../infra
cp terraform.tfvars.example terraform.tfvars     # tu proyecto
terraform init
terraform plan          # revisa: dataset migracion_sas + 5 tablas + bucket + cuenta de servicio
terraform apply
cd ../parte2_gcp
```

Revisa en la consola: **BigQuery > Studio > tu proyecto > migracion_sas**.

## Paso 3 — En real

```bash
# .env con MODO=real
python 17_bigquery/sas_a_bigquery.py
python 17_bigquery/rag_en_bigquery.py "¿cómo saco el promedio por grupo?"
```

En el PASO 3 verás los bytes que leería la consulta (unos cientos de bytes → se factura el mínimo
de 10 MB → ~0.00006 USD, y cae en el TiB gratis).

Consultas útiles para pegar en BigQuery Studio:

```sql
-- ¿Cuánto costaron mis consultas hoy?
SELECT user_email, query, total_bytes_billed / POW(1024, 4) * 6.25 AS usd
FROM `region-us`.INFORMATION_SCHEMA.JOBS
WHERE creation_time > TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), DAY)
ORDER BY usd DESC;

-- Costo de IA por rol (después de: python 21_monitoreo_gobernanza/reporte_costos.py --bigquery)
SELECT rol, modelo, COUNT(*) llamadas, SUM(costo_usd) usd
FROM `TU_PROYECTO.migracion_sas.auditoria_llm`
WHERE DATE(timestamp) = CURRENT_DATE()
GROUP BY rol, modelo ORDER BY usd DESC;
```

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| `404 Not found: Dataset` | No corriste `terraform apply` o `BQ_DATASET` distinto | Aplica Terraform; revisa `.env` |
| `403 ... bigquery.jobs.create` | Falta rol | Tu usuario necesita **BigQuery User** (y Data Editor en el dataset) |
| `Provided Schema does not match` al cargar | CSV con columnas distintas al esquema | Ajusta el CSV o `infra/bigquery.tf` |
| `Could not parse '2026-01-05' as DATE` | Formato de fecha | Usa `AAAA-MM-DD` |
| `Unrecognized name` en el dry run | El LLM inventó una columna | Es la validación funcionando: devuelve el error al LLM |
| `VECTOR_SEARCH` falla por dimensiones | Vectores de modelos distintos en la tabla | Re-carga todo con un solo modelo (WRITE_TRUNCATE) |
| Diferencias al reconciliar | FLOAT64 vs redondeo SAS | Tolerancia; en producción NUMERIC para dinero |
| En simulado: `no such function` | SQLite no conoce funciones de BigQuery | Normal: esas se prueban en real |

## Retos

1. Pide al LLM la versión BigQuery de `inventario.sas` (PROC MEANS) y valídala con dry run.
2. Agrega `maximum_bytes_billed=10**9` al `QueryJobConfig` de `bq.consultar` y explica para qué sirve.
