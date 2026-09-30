# Ejercicio #2 — Listas, diccionarios y ciclos

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #2 de 26** · [← #1 Tu primer script](../01_primer_script/INSTRUCCIONES.md) · [#3 Funciones →](../03_funciones/INSTRUCCIONES.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

**Aprendes:** guardar muchos valores (listas), guardar datos con nombre (diccionarios, la forma
en que llegan las respuestas JSON de un modelo), recorrerlos con `for` y contar cosas.

## #1 — Ejecuta

```bash
python parte0_python/02_listas_y_diccionarios/ejercicio.py
```

## #2 — Lee la demostración

En [ejercicio.py](ejercicio.py), `demostracion()` de `PASO #1` a `PASO #7`. Fíjate especialmente en:
- `PASO #3`: `respuesta["uso"]["tokens_salida"]` → leer un diccionario dentro de otro.
- `PASO #6`: el patrón `conteo[x] = conteo.get(x, 0) + 1`. Lo usarás en el reto #1 y lo verás de nuevo en los micro labs de IA.

## #3 — Resuelve los retos

| Reto | Qué hace | Pista |
|---|---|---|
| #1 `contar_palabras` | `{palabra: veces}` | `.lower().split()` + el patrón del PASO #6 |
| #2 `total_tokens` | suma dos valores anidados | `respuesta["uso"][...]` |
| #3 `mas_frecuente` | la clave con el valor más alto | recorre con `.items()` o usa `max(conteo, key=conteo.get)` |

## #4 — Revisa

Corre de nuevo hasta ver `3 de 3`. Solución: [solucion.py](solucion.py).

## Si algo falla

| Mensaje | Qué significa | Solución |
|---|---|---|
| `KeyError: 'x'` | Esa clave no existe en el diccionario | Revisa el nombre exacto o usa `.get("x", valor_por_defecto)` |
| `IndexError: list index out of range` | Pediste una posición que no existe | Las listas empiezan en 0; la última es `[-1]` |
| `TypeError: 'NoneType' object is not subscriptable` | Algo devolvió `None` y lo usaste como lista/dict | Revisa que tu función tenga `return` |
| `[X ]` con `{'El': 1, 'el': 1, ...}` | No pasaste a minúsculas | `.lower()` antes de `.split()` |

## Palabras nuevas

**lista** `[a, b, c]` valores en orden · **diccionario** `{"clave": valor}` · **for** repetir por
cada elemento · **anidado** una estructura dentro de otra · **JSON** texto con la misma forma que un diccionario.

Anterior: [#1](../01_primer_script/INSTRUCCIONES.md) · Siguiente: **Ejercicio #3** → [03_funciones](../03_funciones/INSTRUCCIONES.md)
