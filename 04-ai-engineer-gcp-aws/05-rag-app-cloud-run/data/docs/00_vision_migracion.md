# Visión del programa de modernización SAS → Python/GCP (Acme Analytics)

Acme Analytics ejecuta el **Programa Helios**, cuyo objetivo es retirar la
plataforma SAS 9.4 on-prem antes del **Q3 de 2027** y migrar toda la lógica
de negocio a Python y Google Cloud Platform.

## Alcance

El programa cubre 312 jobs SAS activos, agrupados en tres dominios:

| Dominio | Jobs SAS | Prioridad | Equivalente destino |
|---|---|---|---|
| Riesgo de crédito | 128 | Alta (regulatorio) | BigQuery SQL + Dataform |
| Reportes financieros | 96 | Media | BigQuery SQL + Looker Studio |
| Marketing y scoring | 88 | Baja | Python (pandas/BigQuery ML) |

## Mapeo de tecnologías

| Componente SAS | Componente destino en GCP |
|---|---|
| DATA step | Python (pandas) o BigQuery SQL, según volumen |
| PROC SQL | BigQuery SQL |
| PROC SORT / PROC MEANS | BigQuery SQL (window functions, `AVG`, `GROUP BY`) |
| SAS/GRAPH, PROC REPORT | Looker Studio |
| SAS Job scheduling (LSF) | Cloud Composer (Airflow) |
| Cargas batch nocturnas grandes | Dataflow (Apache Beam) |
| Librerías compartidas (`%macro`) | Paquetes Python internos, versionados en `acme-migration-libs` |

## Fases del programa

1. **Descubrimiento** (Agente Extractor): parsea el código SAS y genera un
   inventario de reglas de negocio y linaje de datos.
2. **Conversión** (Agente Conversor): genera el equivalente en Python o
   BigQuery SQL a partir del inventario.
3. **Validación** (Agente Validador): compara resultados SAS vs. destino
   (ver `03_proceso_validacion.md`).
4. **Documentación** (Agente Documentador): genera el README y el ADR de
   cada job migrado.

El código de referencia de este mismo laboratorio (05-rag-app-cloud-run) implementa una
versión mínima de un quinto rol: el **Agente de Consulta**, que responde
preguntas sobre estos documentos usando RAG en lugar de tener que leerlos
todos manualmente.
