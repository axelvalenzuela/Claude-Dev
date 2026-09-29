# 13 — Instrucciones

## Paso 1 — Correr

```bash
python 13_embeddings_rag/rag_sas.py
python 13_embeddings_rag/rag_sas.py "¿cómo convierto un IF THEN de SAS?"
```

La primera vez construye el índice y lo guarda en `13_embeddings_rag/.indice_<modo>_<modelo>.json`.

## Paso 2 — Leer el código (`PASO 1` a `PASO 4` en [rag_sas.py](rag_sas.py))

Compara con la parte 1, micro lab 09: es la misma estructura; cambian `vectorizar` (ahora un
modelo) y `generar` (ahora Gemini).

## Qué observar

| Pregunta | Por palabras | Por embeddings |
|---|---|---|
| "¿Cómo quito registros repetidos?" | encuentra `data_step.md` (incorrecto) | encuentra `proc_sort.md` |
| "¿Cuánto cuesta una licencia de SAS?" | — | por debajo del umbral → "No lo sé" |

En simulado, los "embeddings" son un truco con sinónimos escritos a mano
([comun/simulado.py](../comun/simulado.py)). En real, `gemini-embedding-001` aprendió esas
relaciones solo.

## Paso 3 — En real

1. `MODO=real` y corre de nuevo (se crea otro índice, con vectores de ~3,072 dimensiones).
2. **Recalibra `UMBRAL`**: imprime los puntajes de preguntas que SÍ y NO están en la base y pon el
   umbral entre ambos grupos. Con embeddings reales los valores suelen ser más altos que en simulado.

## Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| Siempre "No lo sé" | Umbral muy alto para ese modelo | Recalibra `UMBRAL` |
| Responde con un documento que no tiene que ver | Umbral muy bajo o fragmentos demasiado largos | Sube el umbral; fragmentos más chicos |
| Cambié los documentos y no se nota | Índice cacheado | Borra `.indice_*.json` |
| Resultados raros tras cambiar de modelo | Mezclaste vectores de dos modelos | Nunca mezcles: re-indexa todo |
| Lento al indexar en real | Una llamada por fragmento | Normal aquí; en producción: lotes / Batch |

## Retos

1. Agrega `conocimiento/proc_transpose.md` y pregunta por él.
2. Implementa búsqueda híbrida: puntaje final = 0.7 × embeddings + 0.3 × palabras.
