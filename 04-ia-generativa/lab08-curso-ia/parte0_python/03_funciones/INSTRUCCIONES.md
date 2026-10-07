# Ejercicio #3 — Funciones (y la matemática de los embeddings)

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #3 de 26** · [← #2 Listas y diccionarios](../02_listas_y_diccionarios/INSTRUCCIONES.md) · [#4 Archivos, JSON y errores →](../04_archivos_json_errores/INSTRUCCIONES.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

**Aprendes:** escribir funciones con parámetros y valores por defecto, devolver resultados,
usar funciones dentro de otras, y el módulo `math`. De paso programas la **similitud de coseno**,
la operación con la que se buscan textos parecidos en RAG.

## #1 — Ejecuta

```bash
python parte0_python/03_funciones/ejercicio.py
```

## #2 — Lee la demostración

En [ejercicio.py](ejercicio.py): `PASO #1` (anatomía de una función), `PASO #2` (devolver dos
valores), y en `demostracion()` los pasos `#3` a `#6`. El `PASO #6` (`zip`) es la pista del reto #2.

## #3 — Resuelve los retos, en orden

| Reto | Qué hace | Pista |
|---|---|---|
| #1 `promedio` | suma ÷ cantidad; lista vacía → `0.0` | `if not numeros: return 0.0` |
| #2 `producto_punto` | `a[0]*b[0] + a[1]*b[1] + ...` | `for x, y in zip(a, b)` acumulando en `total` |
| #3 `coseno` | `punto(a,b) / (largo(a) * largo(b))` | `largo(v) = math.sqrt(producto_punto(v, v))` — **reutiliza** tu reto #2 |

## #4 — Revisa

Hasta ver `3 de 3`. Solución: [solucion.py](solucion.py).

Para pensar: `coseno([1, 0], [0.9, 0.1])` da 0.99 (casi iguales); prueba `coseno([1, 0], [0, 1])`.
¿Qué significa un 0? (Respuesta en el ejercicio #11.)

## Si algo falla

| Mensaje | Qué significa | Solución |
|---|---|---|
| `ZeroDivisionError` | Dividiste entre cero (lista vacía en `promedio`) | Revisa el caso vacío primero |
| `TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'` | Una función tuya devolvió `None` | Te falta el `return` en el reto #2 |
| `NameError: name 'math' is not defined` | No importaste el módulo | Ya está `import math` arriba; no lo borres |
| `[X ] devolviste 0.99388...` pero dice error | Diferencia de decimales grande | Revisa la fórmula: la raíz va sobre cada largo, no sobre el resultado |

## Palabras nuevas

**parámetro** el nombre que recibe una función · **argumento** el valor que le pasas ·
**valor por defecto** el que usa si no le pasas nada · **módulo** archivo con funciones listas para importar.

Anterior: [#2](../02_listas_y_diccionarios/INSTRUCCIONES.md) · Siguiente: **Ejercicio #4** → [04_archivos_json_errores](../04_archivos_json_errores/INSTRUCCIONES.md)
