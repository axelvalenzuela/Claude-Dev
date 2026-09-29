# 06 — Embeddings y similitud de coseno

**Idea:** un **embedding** es un vector (lista de números) que representa
el significado de un texto. Textos parecidos → vectores que apuntan en
dirección parecida. La **similitud de coseno** lo mide: 1.0 = iguales,
0.0 = nada que ver.

```bash
python embeddings.py
```

## Qué observar

- **Parte A** (vectores hechos a mano con dimensiones `[animal, fruta, tamaño, doméstico]`):
  lo más parecido a `perro` es `gato` (0.99) y lo menos, `uva` (0.03).
- **Parte B** (vector = conteo de palabras):
  *"un can trota por la plaza"* significa casi lo mismo que
  *"el perro corre en el parque"* pero da **0.00**, y una frase sobre el
  dólar da **0.59** solo por compartir `el` y `en`.

Contar palabras no captura significado. Por eso lab7 usa un **modelo de
embeddings** (`text-embedding-005`) que aprendió de muchísimo texto a
poner `perro` y `can` cerca. Sus vectores tienen ~768 números sin nombre,
pero se comparan con el mismo coseno de aquí
([lab7/src/vector_store.py](../../../lab7/src/vector_store.py)).

## Retos

1. Agrega `"tigre"` a `PALABRAS` con el vector que creas correcto. ¿Sale cerca de `leon`?
2. Agrega una quinta dimensión (`"vuela"`) y la palabra `"aguila"`.

**Siguiente:** cómo un modelo de lenguaje genera texto → [07](../07_siguiente_palabra/)
