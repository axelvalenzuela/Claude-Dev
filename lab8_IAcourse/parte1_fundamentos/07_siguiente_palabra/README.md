# 07 — Un modelo de lenguaje predice la siguiente palabra

**Idea:** Gemini, Claude y GPT hacen, en el fondo, una sola cosa en ciclo:

```
texto hasta ahora ──> probabilidad de cada posible siguiente token ──> escoger uno ──> agregarlo ──> repetir
```

Aquí construimos el modelo de lenguaje más simple: **bigramas**. Solo mira
la última palabra y cuenta qué palabra viene después en el corpus.

```bash
python bigramas.py
```

## Qué observar

- Después de `el`: `gato` 43 %, `perro` 29 %, `parque` 29 %. Eso *es* el modelo: una tabla de probabilidades.
- Algunas frases generadas son nuevas y correctas (no estaban en el corpus).
- Otras no tienen sentido (*"el perro corre en el perro come fruta..."*),
  porque solo recuerda una palabra hacia atrás.

## La diferencia con un LLM real

| Aquí (bigramas) | LLM real |
|---|---|
| Mira 1 palabra atrás | Mira miles de tokens atrás (contexto) |
| Tabla de conteos | Red neuronal gigante (Transformer) |
| 7 frases de entrenamiento | Billones de tokens |

Pero en ambos casos genera lo que **suena probable**, no lo que es
**verdad**. Por eso existen las **alucinaciones**, y por eso existe RAG (micro lab 09).

## Retos

1. Agrega frases al `CORPUS` y vuelve a correr. ¿Mejoran las frases generadas?
2. Cambia `random.seed(3)` y genera otras frases.

**Siguiente:** ¿cómo se escoge el token entre las opciones? → [08](../08_temperatura/)
