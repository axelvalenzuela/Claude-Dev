# Fechas y formatos

SAS guarda las fechas como número de días desde el 1 de enero de 1960. Formatos como DATE9. solo cambian cómo se muestra el valor, no el dato.
En pandas se usa pd.to_datetime y el atributo .dt, por ejemplo df["fecha"].dt.year para YEAR(fecha).
En BigQuery las fechas son tipo DATE y se usan EXTRACT(YEAR FROM fecha) o FORMAT_DATE("%d%b%Y", fecha) para imitar DATE9.
Un error clásico de migración es comparar fechas como texto; hay que convertirlas a tipo fecha antes de filtrar.
