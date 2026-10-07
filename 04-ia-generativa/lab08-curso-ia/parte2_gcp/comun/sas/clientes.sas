/* Clientes activos por año de alta, sin duplicados */
%MACRO clientes_por_anio(anio);
    DATA clientes_&anio;
        SET raw.clientes;
        WHERE YEAR(fecha_alta) = &anio AND activo = 1;
        nombre_completo = CATX(' ', nombre, apellido);
        FORMAT fecha_alta DATE9.;
    RUN;

    PROC SORT DATA=clientes_&anio NODUPKEY;
        BY id_cliente;
    RUN;
%MEND clientes_por_anio;

%clientes_por_anio(2025);
%clientes_por_anio(2026);
