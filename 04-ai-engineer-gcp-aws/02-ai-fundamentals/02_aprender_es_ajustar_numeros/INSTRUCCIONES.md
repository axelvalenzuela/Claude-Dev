# 02 — Instrucciones

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #7 de 26** · [← #6 Reglas vs. aprendizaje](../01_reglas_vs_aprendizaje/README.md) · [#8 Una neurona →](../03_una_neurona/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

## Paso #1 — Ejecuta y observa

```bash
python 02-ai-fundamentals/02_aprender_es_ajustar_numeros/regresion.py
```

Mira la columna `error`: baja rápido y luego casi no cambia.

## Paso #2 — Recorrido guiado del código ([regresion.py](regresion.py))

1. `predecir`: el modelo entero es `w * horas + b`.
2. `error_promedio`: qué tan lejos están las predicciones de la realidad (error cuadrático medio).
3. `main`, `PASO #2`: `grad_w` y `grad_b` dicen hacia dónde sube el error; restamos para bajar.
4. `TASA_APRENDIZAJE`: el tamaño del paso. Es el "hiperparámetro" más importante.

## Paso #3 — Experimento guiado

Cambia `TASA_APRENDIZAJE` a `0.05` y luego a `0.1`. Con `0.1` el error crece hasta volverse enorme
(o `nan`): el paso es tan grande que "brinca" el mínimo. Así se ve un entrenamiento que **diverge**.

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| `error` se vuelve `inf` o `nan` | Tasa de aprendizaje muy alta | Bájala |
| El error baja muy lento | Tasa muy baja o pocas épocas | Súbela un poco o aumenta `EPOCAS` |

## Autoevaluación

¿Qué es un "parámetro" y qué es "entrenar"? Explícalo con `w` y `b`.
