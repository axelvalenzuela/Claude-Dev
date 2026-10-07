# PROC MEANS y estadísticas por grupo

PROC MEANS calcula estadísticas descriptivas como suma (SUM), media (MEAN), mínimo y máximo. CLASS define los grupos y VAR las variables a resumir; OUTPUT OUT= guarda el resultado en una tabla.
En pandas: df.groupby("categoria").agg(valor_total=("valor", "sum"), valor_prom=("valor", "mean")).
En BigQuery: SELECT categoria, SUM(valor), AVG(valor) FROM tabla GROUP BY categoria.
Detalle importante: OUTPUT OUT= de PROC MEANS agrega una fila de total general (_TYPE_ = 0) y las columnas _TYPE_ y _FREQ_; hay que decidir si la migración las replica.
