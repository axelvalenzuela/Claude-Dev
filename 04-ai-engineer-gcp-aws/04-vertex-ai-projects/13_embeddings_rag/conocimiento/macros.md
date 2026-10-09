# Macros de SAS

Las macros (%MACRO ... %MEND) son plantillas de código con parámetros, como &anio. Se usan para reutilizar la misma lógica con distintas variables o para generar código repetitivo.
En Python una macro normalmente se convierte en una función con parámetros: def clientes_por_anio(df, anio).
Las variables de macro globales (%LET) se convierten en constantes o en configuración leída de variables de entorno.
Las macros son de lo más difícil de migrar automáticamente porque generan código dinámico: el análisis debe expandirlas primero para conocer el código real que se ejecuta.
