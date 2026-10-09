# Ejercicio #4 — Archivos, CSV, JSON y errores

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #4 de 26** · [← #3 Funciones](../03_funciones/INSTRUCCIONES.md) · [#5 Clases y tipos →](../05_clases_y_tipos/INSTRUCCIONES.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

**Aprendes:** importar módulos, leer archivos de texto y CSV, convertir JSON ↔ diccionario, y
atrapar errores con `try/except` para que tu programa no truene cuando un modelo responde mal.

## #1 — Ejecuta

```bash
python 01-python-for-ai/04_archivos_json_errores/ejercicio.py
```

Usa el archivo `04-vertex-ai-projects/comun/datos/ventas.csv`: la misma tabla que migraremos desde SAS en la parte 2.

## #2 — Lee la demostración

En [ejercicio.py](ejercicio.py), `PASO #1` a `PASO #5`. Lo más importante:
- `PASO #3`: del CSV **todo llega como texto**; `"12000"` se convierte con `float("12000")`.
- `PASO #5`: `try/except` atrapa el JSON roto en vez de tronar.

## #3 — Resuelve los retos

| Reto | Qué hace | Pista |
|---|---|---|
| #1 `leer_json` | JSON → dict; si falla, `{"error": "json invalido"}` | `try: return json.loads(texto)` / `except json.JSONDecodeError:` |
| #2 `ventas_completadas` | cuenta filas con estado `COMPLETADA` | `with open(ruta, encoding="utf-8") as archivo:` + `csv.DictReader(archivo)` |
| #3 `total_completadas` | suma los montos de esas filas | `total += float(fila["monto"])` |

## #4 — Revisa

Hasta ver `3 de 3`. Solución: [solucion.py](solucion.py).

## Si algo falla

| Mensaje | Qué significa | Solución |
|---|---|---|
| `FileNotFoundError` | La ruta no existe | Corre desde la raíz del repo y no muevas `04-vertex-ai-projects/` |
| `UnicodeDecodeError` | Leíste sin la codificación correcta | Siempre `encoding="utf-8"` |
| `TypeError: can only concatenate str (not "float")` | Sumaste texto con número | Convierte con `float()` |
| `[X ] devolviste '12000350087...'` | Sumaste textos (se pegan) | Mismo caso: `float()` |
| `json.decoder.JSONDecodeError` sin atrapar | Falta el `except` | Revisa la sangría del `try/except` |

## Palabras nuevas

**import** traer un módulo · **CSV** tabla en texto separada por comas · **JSON** formato de datos
de las APIs · **excepción** un error que puedes atrapar · **with** abre y cierra un archivo automáticamente.

Anterior: [#3](../03_funciones/INSTRUCCIONES.md) · Siguiente: **Ejercicio #5** → [05_clases_y_tipos](../05_clases_y_tipos/INSTRUCCIONES.md)
