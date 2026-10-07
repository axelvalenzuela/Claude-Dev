# 07 — Instrucciones

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #12 de 26** · [← #11 Embeddings](../06_embeddings/README.md) · [#13 Temperatura →](../08_temperatura/README.md) · [ruta completa](../../EMPIEZA_AQUI.md)
<!-- ruta:fin -->

## Paso #1 — Ejecuta y observa

```bash
python parte1_fundamentos/07_siguiente_palabra/bigramas.py
```

## Paso #2 — Recorrido guiado del código ([bigramas.py](bigramas.py))

1. `entrenar`: para cada par de palabras seguidas, `siguientes[actual][siguiente] += 1`.
2. `probabilidades`: conteos → porcentajes.
3. `generar`: el ciclo de todo LLM: escoger, agregar, repetir hasta `"."`.

## Paso #3 — Experimento guiado

Agrega 5 frases propias al `CORPUS` sobre otro tema (p. ej. comida). Genera frases. ¿Aparecen
mezclas absurdas entre temas? Es una "alucinación" en miniatura.

## Si algo falla

| Síntoma | Solución |
|---|---|
| Error al generar / lista vacía | Una frase del corpus no termina en `" ."`: agrega el punto separado por un espacio |

## Autoevaluación

Si un LLM solo predice lo más probable, ¿por qué no podemos confiar ciegamente en lo que dice?
