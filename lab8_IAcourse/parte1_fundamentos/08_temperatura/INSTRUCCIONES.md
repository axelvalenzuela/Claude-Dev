# 08 — Instrucciones

## Paso 1 — Ejecuta y observa

```bash
python parte1_fundamentos/08_temperatura/temperatura.py
```

## Paso 2 — Recorrido guiado del código ([temperatura.py](temperatura.py))

1. `LOGITS`: los puntajes crudos del modelo.
2. `softmax`: divide entre la temperatura, aplica `exp` y normaliza a 100 %. Restar el máximo evita desbordes.
3. `random.choices(..., weights=...)`: escoger según las probabilidades.

## Paso 3 — Experimento guiado

Agrega `0.05` y `5.0` a la lista de temperaturas. Con 0.05 siempre sale `azul`; con 5.0 casi todo
es igual de probable.

## Si algo falla

| Síntoma | Solución |
|---|---|
| `ZeroDivisionError` | Pusiste temperatura 0. "Temperatura 0" en la práctica significa escoger el máximo directamente |

## Autoevaluación

¿Qué temperatura usarías para convertir código? ¿Y para lluvia de ideas? (Ojo: en Gemini 3 la
recomendación cambió; ver parte 2, lab 11.)
