# PROC SORT y registros duplicados

PROC SORT ordena una tabla por las variables del BY. Con la opción NODUPKEY además elimina los registros duplicados que comparten la misma llave BY y se queda con el primero.
En pandas: df.sort_values("id_cliente").drop_duplicates(subset=["id_cliente"], keep="first").
En BigQuery se usa QUALIFY ROW_NUMBER() OVER (PARTITION BY id_cliente ORDER BY ...) = 1 para quedarse con una fila por llave.
Ojo: NODUPKEY depende del orden previo de los datos; si la migración no fija el mismo orden, puede quedarse con otro registro distinto y la reconciliación falla.
