/* Reporte de ventas por región: solo ventas completadas, con IVA (16%) */
DATA ventas_limpias;
    SET raw.ventas;
    WHERE estado = 'COMPLETADA';
    total_con_iva = monto * 1.16;
    IF total_con_iva > 10000 THEN categoria = 'ALTA';
    ELSE categoria = 'NORMAL';
RUN;

PROC SQL;
    CREATE TABLE resumen_ventas AS
    SELECT region,
           categoria,
           COUNT(*) AS num_ventas,
           SUM(total_con_iva) AS total
    FROM ventas_limpias
    GROUP BY region, categoria;
QUIT;
