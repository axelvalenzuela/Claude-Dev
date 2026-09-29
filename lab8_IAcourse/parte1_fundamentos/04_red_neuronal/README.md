# 04 — Red neuronal (XOR resuelto)

**Idea:** si una neurona solo traza una recta, **varias neuronas en capas**
pueden combinar varias rectas y separar formas más complicadas.

```
entrada (2) ──> capa oculta (3 neuronas) ──> salida (1)
```

Para entrenar, el error de la salida se reparte **hacia atrás** a cada
peso según cuánto contribuyó: eso es **backpropagation**, el algoritmo con
el que se entrenan todas las redes modernas, incluidos los LLM.

```bash
python red_xor.py
```

## Qué observar

- Antes de entrenar la red responde ~0.3 para todo (pesos al azar).
- El error baja de ~0.28 a ~0.0003.
- Al final responde 0.016 / 0.983 / 0.983 / 0.021: no 0 y 1 exactos, sino
  **probabilidades**. Guarda esta idea para el micro lab 07.

## Retos

1. Pon `OCULTAS = 1`. Con una sola neurona oculta vuelve a fallar.
2. Cambia `random.seed(7)` por otro número. A veces tarda más o se atora:
   el punto de partida importa.
3. Pon `EPOCAS = 500`. ¿Qué tan bien quedó?

**Siguiente:** ya sabemos qué es una red neuronal. Ahora, ¿cómo le metemos
**texto**? → [05](../05_tokens/)
