/* Estadísticas de inventario por categoría */
DATA inventario;
    SET raw.inventario;
    valor = cantidad * costo_unitario;
    IF cantidad < 10 THEN alerta = 'REORDENAR';
RUN;

PROC MEANS DATA=inventario NOPRINT;
    CLASS categoria;
    VAR valor cantidad;
    OUTPUT OUT=resumen_inventario SUM=valor_total cantidad_total MEAN=valor_prom cantidad_prom;
RUN;
