# 03 — Instrucciones

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #8 de 26** · [← #7 Aprender = ajustar números](../02_aprender_es_ajustar_numeros/README.md) · [#9 Red neuronal →](../04_red_neuronal/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

## Paso #1 — Ejecuta y observa

```bash
python 02-ai-fundamentals/03_una_neurona/perceptron.py
```

## Paso #2 — Recorrido guiado del código ([perceptron.py](perceptron.py))

1. `neurona`: suma ponderada + sesgo, y decide 1 o 0.
2. `entrenar`: si se equivoca, `error` es +1 o -1 y los pesos se empujan en esa dirección.
3. Si en una época no hay errores, terminó (`return ... epoca`).

## Paso #3 — Experimento guiado

Dibuja en papel los 4 puntos (0,0), (0,1), (1,0), (1,1). Marca con X los que dan 1 en AND y traza
una recta que los separe de los demás. Ahora hazlo con XOR. No se puede: por eso falla.

## Si algo falla

| Síntoma | Solución |
|---|---|
| XOR "no aprende" | ¡Es lo esperado! Es la lección del lab |
| Otra compuerta que agregaste tampoco aprende | Revisa la tabla; sube `epocas` |

## Autoevaluación

¿Qué le falta a una sola neurona para resolver XOR? (Respuesta en el ejercicio 04.)
