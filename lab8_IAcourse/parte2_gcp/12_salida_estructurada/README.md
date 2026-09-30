# 12 — Salida estructurada: extraer reglas de negocio de SAS

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #17 de 26** · [← #16 Gemini con el SDK](../11_gemini_sdk/README.md) · [#18 RAG con embeddings →](../13_embeddings_rag/README.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

**Qué aprendes:** hacer que el modelo responda JSON con una forma fija y validarlo.
Es la base de cualquier agente que alimenta a otro programa.

## Conceptos

```
Pydantic (AnalisisSAS) ──> response_schema ──> Gemini responde JSON ──> model_validate_json ──> objeto Python
                                                                              │
                                                                   si no cumple: ValidationError
```

- **Esquema** ([comun/esquemas.py](../comun/esquemas.py)): `AnalisisSAS` con `reglas: list[ReglaNegocio]`,
  cada regla con `tipo` (`Literal[...]`, se vuelve un *enum* que el modelo no puede inventar) y
  `codigo_sas` (el fragmento de origen: **trazabilidad** para auditoría).
- **`response_schema` + `response_mime_type="application/json"`**: el modelo se restringe a esa forma.
- **Validar igual**: el esquema reduce errores pero no los elimina (campos vacíos, reglas inventadas).
  Validar con Pydantic hace que el error truene aquí y no tres pasos después.

## Para la entrevista

- *"¿Cómo extraes reglas de negocio de código legacy?"* → agente analista con salida
  estructurada, cada regla con su fragmento de origen, validación de esquema, y medición de
  recall contra un golden set (lab 16).
- *"¿Qué haces si el JSON no valida?"* → reintentar incluyendo el error en el prompt, y si
  persiste, mandarlo a revisión humana. Nunca "arreglarlo" en silencio.

Siguiente: [INSTRUCCIONES.md](INSTRUCCIONES.md)
