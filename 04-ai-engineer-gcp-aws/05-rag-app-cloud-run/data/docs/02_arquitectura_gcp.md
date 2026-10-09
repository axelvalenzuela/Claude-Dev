# Arquitectura GCP del Programa Helios

## Proyectos

| Proyecto GCP | Uso |
|---|---|
| `acme-helios-dev` | Desarrollo y pruebas de los agentes |
| `acme-helios-prd` | Ejecución de las migraciones aprobadas |

## Servicios y su rol

- **Vertex AI (Gemini + text-embedding-005)**: motor de los cuatro agentes
  (Extractor, Conversor, Validador, Documentador) y del Agente de Consulta
  de este laboratorio. Todas las llamadas pasan por el proyecto
  `acme-helios-dev` en la región `us-central1`.
- **Cloud Run**: hospeda cada agente como un servicio HTTP independiente
  (`agente-extractor`, `agente-conversor`, `agente-validador`,
  `agente-documentador`, `agente-consulta`), sin servidores que mantener y
  escalando a cero fuera de horario de migración.
- **Cloud Composer**: orquesta el pipeline completo (Extractor → Conversor
  → Validador → Documentador) como un DAG de Airflow, un job SAS a la vez.
- **Dataflow**: se usa únicamente para las cargas batch nocturnas del
  dominio "Reportes financieros" (>50 GB), donde pandas en memoria no
  alcanza.
- **BigQuery**: destino final de todos los datos migrados. Un dataset por
  dominio: `riesgo_credito`, `reportes_financieros`, `marketing_scoring`.
- **Cloud Storage**: bucket `acme-helios-artifacts` guarda el código SAS
  fuente, los datasets dorados de validación y los reportes de
  reconciliación.

## Convención de nombres de recursos

Todo recurso creado por el programa lleva el prefijo `helios-`, por
ejemplo: `helios-agente-extractor`, `helios-bq-riesgo-credito`. Los
recursos sin ese prefijo se consideran fuera del programa y no deben
tocarse desde las pipelines de Helios.

## Vector de conocimiento

Para el volumen actual (312 jobs, unas 900 páginas de documentación), el
programa usa una base vectorial en memoria (como la de este laboratorio)
regenerada en cada despliegue. Si el número de documentos supera ~5,000
chunks, el estándar interno pasa a usar **Vertex AI Vector Search** con un
índice persistente, para no pagar el costo de reembeber todo en cada
arranque.
