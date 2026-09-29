# 14 — Instrucciones

## Paso 1 — Correr

```bash
python 14_agente_herramientas/agente.py
python 14_agente_herramientas/agente.py "¿Qué hace clientes.sas y cómo lo migro?"
```

## Paso 2 — Leer el código

1. [herramientas.py](herramientas.py): lee cada docstring como si fueras el modelo. ¿Sabrías cuándo usar cada una?
2. [agente.py](agente.py): `PASO 1`, `PASO 2`, `PASO 3` y `MAX_PASOS`.
3. [comun/llm.py](../comun/llm.py): clase `SesionAgente` → `enviar`, `enviar_resultados`, `_turno`.

## Qué observar

- Paso 1: pide la lista. Paso 2: pide 3 herramientas **a la vez**. Paso 3: busca equivalencias. Luego responde.
- En simulado el orden es un guion fijo. En real, Gemini decide: con la segunda pregunta
  probablemente use `leer_programa_sas`, que el guion nunca usa.

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| "Me detuve: se alcanzó el límite" | El modelo no converge | Mejora docstrings; instrucción de sistema más concreta; sube `MAX_PASOS` con cuidado |
| El modelo inventa en vez de usar herramientas | La instrucción no lo exige | "Usa las herramientas; nunca adivines" (ya está) y modelos más capaces |
| `TypeError: got an unexpected keyword argument` | El modelo mandó argumentos con otro nombre | Nombres de parámetros claros; el error vuelve al modelo y suele corregirse |
| `400 ... function response` en real | Historial mal armado | No modifiques el turno del modelo; devuelve un resultado por cada llamada |
| Herramienta lenta | E/S pesada | Timeouts dentro de la herramienta; resultados resumidos (no archivos enteros) |

## Retos

1. Agrega la herramienta `estimar_horas_migracion(nombre_programa: str) -> int` (p. ej. puntaje × 4) y pregunta cuánto tardaría migrar todo.
2. Haz que una herramienta truene a propósito y observa cómo reacciona el modelo en real.
