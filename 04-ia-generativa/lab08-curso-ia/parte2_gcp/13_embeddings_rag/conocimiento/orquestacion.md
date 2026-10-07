# Calendarización y orquestación

En SAS los procesos se calendarizan con SAS Management Console, cron o scripts que ejecutan programas en secuencia.
En Google Cloud el equivalente administrado es Cloud Composer, que es Apache Airflow: cada proceso se define como un DAG de tareas con dependencias, reintentos y alertas.
Para eventos (por ejemplo, llega un archivo nuevo a un bucket) conviene Cloud Functions o Eventarc en lugar de calendarizar.
Para transformaciones pesadas de datos en paralelo se usa Dataflow (Apache Beam) o directamente SQL en BigQuery.
