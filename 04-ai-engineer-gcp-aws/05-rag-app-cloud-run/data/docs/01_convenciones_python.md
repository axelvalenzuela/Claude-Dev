# Convenciones de código para módulos migrados (Python)

Todo módulo Python generado por el Agente Conversor dentro del Programa
Helios debe seguir estas reglas antes de poder entrar a revisión humana.

## Cabecera obligatoria

Cada archivo migrado empieza con un bloque de trazabilidad hacia el job SAS
original:

```python
# origen-sas: SAS-4821
# job-original: /sasprod/riesgo/calc_perdida_esperada.sas
# migrado-por: agente-conversor v2
# revisado-por: <nombre humano, pendiente hasta aprobación>
```

El identificador `origen-sas` sigue siempre el formato `SAS-####` y debe
existir como ticket en el proyecto Jira **HELIOS** antes de fusionar el
cambio.

## Estructura de carpetas

```
migrations/<dominio>/<job_id>/
├── README.md          # qué hacía el job SAS, en una frase
├── convert.py          # lógica migrada
├── convert_test.py      # pruebas contra el dataset dorado (ver validación)
└── adr.md              # decisiones de diseño tomadas en la conversión
```

## Reglas de estilo

- Formateo con `ruff format`, sin excepciones.
- Nombres de columnas siempre en `snake_case`, aunque el SAS original use
  mayúsculas (SAS no distingue mayúsculas/minúsculas; Python sí).
- Ningún módulo migrado puede superar 400 líneas: si el job SAS original es
  más grande, se divide en submódulos por macro.
- Las consultas a BigQuery se escriben con la librería interna
  `acme_bq_client`, nunca con `google-cloud-bigquery` directo, para heredar
  el retry y el logging estándar del equipo.

## Aprobación

Un módulo migrado solo puede fusionarse a `main` cuando el Agente
Validador reporta una reconciliación **PASA** (ver
`03_proceso_validacion.md`) y un revisor humano del dominio correspondiente
aprueba el pull request.
