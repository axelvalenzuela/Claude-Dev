# 06 — Instrucciones

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #11 de 26** · [← #10 Tokens](../05_tokens/README.md) · [#12 Siguiente palabra →](../07_siguiente_palabra/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

## Paso #1 — Ejecuta y observa

```bash
python 02-ai-fundamentals/06_embeddings/embeddings.py
```

## Paso #2 — Recorrido guiado del código ([embeddings.py](embeddings.py))

1. `PALABRAS`: vectores hechos a mano; cada posición tiene un significado.
2. `coseno`: producto punto dividido entre las longitudes. 1 = misma dirección.
3. `parte_a`: ranking de parecido. `parte_b`: el mismo coseno, pero con vectores de conteo de palabras.

## Paso #3 — Experimento guiado

Calcula a mano el coseno entre `perro` [1, 0, 0.5, 1] y `gato` [1, 0, 0.3, 1]:
punto = 1 + 0 + 0.15 + 1 = 2.15; longitudes ≈ 1.5 y 1.446; coseno ≈ 0.99. Compara con la salida.

## Si algo falla

| Síntoma | Solución |
|---|---|
| `ZeroDivisionError` | Un vector de puros ceros: `coseno` ya devuelve 0.0 en ese caso; revisa que no hayas quitado ese `if` |

## Autoevaluación

¿Por qué "un can trota por la plaza" da 0 con conteo de palabras? ¿Qué lo arregla? (parte 2, ejercicio 13)
