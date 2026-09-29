# 05 — Tokens

**Idea:** una red neuronal solo procesa números. El texto se corta en
**tokens** (pedazos) y cada token recibe un id numérico. Los modelos
actuales usan **subpalabras**, aprendidas juntando los pares de letras
más frecuentes (algoritmo **BPE**).

```bash
python tokens.py
```

## Qué observar

- Las fusiones aprendidas: `g+r → gr`, `gr+a → gra`… hasta formar `programa` y `migra`,
  porque son lo que más se repite en el corpus.
- La misma frase cuesta 30 tokens por letra, 5 por palabra, 13 con BPE.
- `reprogramador` nunca apareció, pero se arma con piezas conocidas
  (`r`, `e`, `programa`, `d`, `or`). Así un modelo maneja palabras nuevas.

## Por qué te importa

Los modelos **cobran por token** y tienen un **límite de tokens** (la
"ventana de contexto"). En lab7, [src/count_tokens.py](../../../lab7/src/count_tokens.py)
le pregunta a Gemini cuántos tokens gasta una pregunta.

## Retos

1. Sube `FUSIONES` a 30. ¿Qué pasa con el número de tokens de la frase?
2. Tokeniza una palabra en inglés. Como el corpus es en español, sale en muchos pedazos.

**Siguiente:** ya tenemos tokens como números. ¿Cómo se representa el
**significado**? → [06](../06_embeddings/)
