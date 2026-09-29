# 02 — Aprender = ajustar números

**Idea:** un modelo es una fórmula con **parámetros**. Entrenar es
repetir *predecir → medir el error → mover los parámetros un poquito para
que el error baje*. Eso se llama **descenso de gradiente**.

Aquí el modelo es una recta: `calificacion = w * horas + b` (2 parámetros).
Gemini tiene miles de millones, pero se entrena con la misma idea.

```bash
python regresion.py
```

## Qué observar

- En la época 0, `w = 0`, `b = 0` y el error es enorme (~4650).
- El error baja rápido al principio y luego casi no cambia: el modelo **convergió**.
- Con 10 horas predice más de 100. El modelo no "entiende" que hay un
  tope: solo repite el patrón que vio. Los LLM tienen este mismo problema
  a otra escala.

## Retos

1. Cambia `TASA_APRENDIZAJE` a `0.1`. El error **explota** en vez de bajar:
   los pasos son tan grandes que se pasa del mínimo cada vez.
2. Pon `TASA_APRENDIZAJE = 0.001`. Aprende, pero mucho más lento.
3. Pon `EPOCAS = 50`. El modelo queda a medio entrenar.

**Siguiente:** [03](../03_una_neurona/) usa esta misma idea para tomar decisiones sí/no.
