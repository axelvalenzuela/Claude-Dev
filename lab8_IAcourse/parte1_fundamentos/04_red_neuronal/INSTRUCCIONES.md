# 04 — Instrucciones

## Paso 1 — Ejecuta y observa

```bash
python parte1_fundamentos/04_red_neuronal/red_xor.py
```

## Paso 2 — Recorrido guiado del código ([red_xor.py](red_xor.py))

1. Pesos iniciales al azar (`random.uniform`): si fueran 0, todas las neuronas aprenderían lo mismo.
2. `adelante`: entrada → capa oculta (3 sigmoides) → salida (1 sigmoide).
3. `entrenar`, pasos 1-2-3: error de la salida → repartir la culpa hacia atrás → ajustar cada peso.
   Eso es **backpropagation**.
4. `main`: `PASO 1` antes, `PASO 2` entrenar, `PASO 3` después.

## Paso 3 — Experimento guiado

1. `OCULTAS = 1` → vuelve a fallar (una neurona oculta es casi una sola recta).
2. `OCULTAS = 3` con `random.seed(1)`, `seed(2)`... ¿todas convergen igual de rápido?

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| El error se queda en ~0.25 | La red quedó atorada (mínimo local) | Cambia la semilla o sube `OCULTAS` |
| `OverflowError` en `math.exp` | Pesos enormes por `TASA` alta | Baja `TASA` |

## Autoevaluación

¿Qué significa que la salida sea 0.983 y no 1? ¿Dónde vuelves a ver esa idea? (micro lab 07)
