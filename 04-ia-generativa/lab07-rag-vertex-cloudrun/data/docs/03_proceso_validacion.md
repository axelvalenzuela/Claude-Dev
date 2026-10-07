# Proceso de validación de migraciones (Agente Validador)

## Dataset dorado

Antes de migrar un job SAS, el equipo de dominio congela un **dataset
dorado**: la salida exacta del job SAS original corriendo sobre un
snapshot fijo de datos de entrada. Vive en
`gs://acme-helios-artifacts/golden/<job_id>/`.

## Umbrales de reconciliación

El Agente Validador compara, fila por fila, la salida del código migrado
contra el dataset dorado:

| Tipo de columna | Umbral máximo de diferencia |
|---|---|
| Numérica (montos, tasas) | 0.01% de diferencia relativa |
| Fecha | Coincidencia exacta |
| Texto / categórica | Coincidencia exacta, salvo mapeo de catálogo documentado en el ADR |
| Conteo de filas | Coincidencia exacta |

Si cualquier columna numérica supera 0.01% de diferencia, o si hay
cualquier diferencia en fechas, texto o conteo de filas, el resultado es
**FALLA** y el pull request no puede fusionarse.

## Veredictos posibles

- **PASA**: todas las columnas dentro de umbral. Puede pasar a revisión
  humana.
- **PASA CON OBSERVACIONES**: dentro de umbral, pero el Agente Validador
  detectó un patrón sospechoso (por ejemplo, una columna que en SAS tenía
  valores nulos representados como `.` y en Python quedó como `NaN` sin
  documentar la equivalencia). Requiere que un humano confirme antes de
  fusionar.
- **FALLA**: fuera de umbral en al menos una columna. Regresa
  automáticamente al Agente Conversor con el detalle de las filas que no
  coinciden.

## Reintentos

El Agente Conversor tiene un máximo de **3 reintentos automáticos** por
job antes de que el caso se escale a un ingeniero humano del equipo
Helios. Cada reintento debe adjuntar el diff de las filas que fallaron en
el intento anterior como parte del prompt de corrección.
