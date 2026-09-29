# DATA step

El DATA step de SAS procesa una tabla fila por fila. SET lee la tabla de entrada, WHERE filtra registros y las asignaciones crean columnas nuevas.
En pandas el equivalente es trabajar con el DataFrame completo: df[df["estado"] == "COMPLETADA"] para el WHERE y df["nueva"] = df["a"] * 1.16 para las columnas calculadas.
En BigQuery SQL el DATA step suele convertirse en un SELECT con WHERE y expresiones, o en un CTE (WITH) cuando hay varios pasos.
IF ... THEN ... ELSE se traduce a numpy.where o Series.map en pandas, y a CASE WHEN en BigQuery.
Cuidado: SAS trata los valores faltantes numéricos como menores que cualquier número; pandas usa NaN y las comparaciones con NaN dan False.
