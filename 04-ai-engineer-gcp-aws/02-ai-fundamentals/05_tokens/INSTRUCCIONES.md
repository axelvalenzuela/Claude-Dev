# 05 — Instrucciones

<!-- ruta:inicio -->
> **Ruta de aprendizaje: ejercicio #10 de 26** · [← #9 Red neuronal](../04_red_neuronal/README.md) · [#11 Embeddings →](../06_embeddings/README.md) · [ruta completa](../../EMPIEZA-AQUI.md)
<!-- ruta:fin -->

## Paso #1 — Ejecuta y observa

```bash
python 02-ai-fundamentals/05_tokens/tokens.py
```

## Paso #2 — Recorrido guiado del código ([tokens.py](tokens.py))

1. `aprender_bpe`: cada palabra empieza como letras sueltas; en cada paso se juntan los dos
   símbolos que más aparecen juntos (`contar_pares` → `fusionar`).
2. `tokenizar`: aplica las mismas fusiones, en el mismo orden, a texto nuevo.
3. `vocab`: cada token distinto recibe un número. Eso es lo que "ve" la red neuronal.

## Paso #3 — Experimento guiado

Pon `FUSIONES = 3` y luego `30`. Anota cuántos tokens da la frase en cada caso. Más fusiones =
vocabulario más grande y textos más cortos (en tokens).

## Si algo falla

| Síntoma | Solución |
|---|---|
| Se detiene antes de llegar a `FUSIONES` | Ya no quedan pares para fusionar: el corpus es chico |

## Autoevaluación

¿Por qué a una empresa le importa si su texto usa 1.3 o 2 tokens por palabra?
