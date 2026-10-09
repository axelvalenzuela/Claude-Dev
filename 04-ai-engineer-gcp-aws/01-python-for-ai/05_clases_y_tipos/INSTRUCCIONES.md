# Ejercicio #5 — Clases, dataclasses y type hints

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #5 de 26** · [← #4 Archivos, JSON y errores](../04_archivos_json_errores/INSTRUCCIONES.md) · [#6 Reglas vs. aprendizaje →](../../02-ai-fundamentals/01_reglas_vs_aprendizaje/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

**Aprendes:** leer y escribir clases, porque el SDK de Gemini, Pydantic y los agentes de la parte 2
están hechos con ellas. Después de este ejercicio podrás leer `04-vertex-ai-projects/comun/llm.py`.

## #1 — Ejecuta

```bash
python 01-python-for-ai/05_clases_y_tipos/ejercicio.py
```

## #2 — Lee la demostración

En [ejercicio.py](ejercicio.py):
- `PASO #1`: type hints (`tokens: int`, `-> float`): documentan qué tipo entra y sale.
- `PASO #2` y `#3`: `@dataclass Respuesta` y su método `total_tokens(self)`.
- `PASO #4`: `AgenteEco` guarda un `historial` que crece con cada mensaje: la idea de "memoria" de un agente.
- `PASO #5`: Pydantic = dataclass + validación (lo verás en el ejercicio #17).

Clave: **`self`** es "este objeto". Dentro de un método, `self.tokens_entrada` es el dato de *ese* objeto.

## #3 — Resuelve los retos

| Reto | Qué hace | Pista |
|---|---|---|
| #1 `Llamada.costo` | costo de una llamada | usa `self.tokens_entrada` y `self.tokens_salida` |
| #2 `total_costos` | suma el costo de varias | `for llamada in llamadas: total += llamada.costo(...)` |
| #3 `Memoria` | guardar mensajes y devolver los últimos n | `self.mensajes.append(...)` y `self.mensajes[-n:]` |

## #4 — Revisa

Hasta ver `3 de 3`. Solución: [solucion.py](solucion.py).

**Terminaste la parte 0.** Ya tienes el Python necesario para los micro labs de IA.

## Si algo falla

| Mensaje | Qué significa | Solución |
|---|---|---|
| `NameError: name 'tokens_entrada' is not defined` | Dentro del método olvidaste `self.` | `self.tokens_entrada` |
| `TypeError: costo() missing 1 required positional argument` | Llamaste al método con menos datos | `llamada.costo(precio_entrada, precio_salida)` |
| `AttributeError: 'Llamada' object has no attribute 'x'` | Ese atributo no existe | Revisa el nombre en la definición de la clase |
| `[X ] devolviste ['gracias']` | Te faltó un mensaje | `[-n:]` con `n=2` devuelve los últimos 2 |

## Palabras nuevas

**clase** molde para crear objetos · **objeto** una "cosa" creada con ese molde · **atributo**
dato del objeto · **método** función del objeto · **`self`** el propio objeto · **type hint** anotación del tipo.

Anterior: [#4](../04_archivos_json_errores/INSTRUCCIONES.md) · Siguiente: **Ejercicio #6** → [02-ai-fundamentals/01_reglas_vs_aprendizaje](../../02-ai-fundamentals/01_reglas_vs_aprendizaje/README.md)
