# 20 — Cloud Composer (Airflow) y Dataflow (Apache Beam)

**Qué aprendes:** los dos destinos de "modernización" que pide la vacante: el proceso SAS
convertido en un **pipeline de Dataflow**, y la calendarización SAS convertida en un **DAG de Composer**.

## Conceptos

**Dataflow / Apache Beam** — [pipeline_ventas_beam.py](pipeline_ventas_beam.py)

```
ReadFromText ─> Map(parsear) ─> Filter(COMPLETADA) ─> Map(IVA+categoría) ─> CombinePerKey(contar,sumar) ─> WriteToText
   (SET)                          (WHERE)               (asignaciones, IF)       (PROC SQL GROUP BY)
```

- **PCollection** = datos distribuidos; **PTransform** = paso. El mismo código corre local (runner
  Prism, gratis) o en Dataflow (`--runner DataflowRunner`), donde Google levanta y apaga máquinas.
- **CombineFn**: agregación que se puede calcular en paralelo y luego juntar (`merge_accumulators`).
- Al final se **reconcilia** contra la salida de SAS, igual que en los labs 15 y 17.

**Cloud Composer / Airflow** — [dag_migracion_sas.py](dag_migracion_sas.py)

```
listar_programas ─> migrar_programa.expand(...)  (1 tarea por programa, en paralelo, llama a Cloud Run)
                                    └─> cargar_reporte_a_bigquery
```

- **DAG**: tareas + dependencias + calendario (`schedule`) + reintentos (`retries`).
- **Dynamic task mapping** (`.expand`): tantas tareas como programas encuentre.
- **`max_active_tasks`**: también es un control de costo (llamadas simultáneas a la IA).
- Composer 3 cuesta **~400 USD/mes** aunque no corra nada: en entrevista, saber *cuándo no usarlo*
  (flujos simples → Cloud Scheduler + Cloud Run / Workflows) también cuenta.

## Para la entrevista

- *"¿Cómo migrarías los jobs calendarizados de SAS?"* → inventario de jobs y dependencias → DAGs
  en Composer que llaman a lo migrado (BigQuery SQL, Dataflow, Cloud Run) con reintentos y alertas.
- *"¿Dataflow o BigQuery?"* → si se expresa en SQL, BigQuery; streaming o lógica compleja, Dataflow.

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
